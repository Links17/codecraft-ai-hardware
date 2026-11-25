"""Repository-only CI planning and result aggregation; never run native operations."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import io
import json
import os
from pathlib import Path
import re
import subprocess
import tarfile
import tempfile

from ci_policy import host_only
from graph import SourceGraph
from io_utils import parse_json, read_json, require, result, safe_path, write_json
from model import native_roots
from registry import load_group
from render import matrix


def git(root, *args, check=True):
    run = subprocess.run(['git', '-C', str(root), *args], capture_output=True)
    require(not check or run.returncode == 0,
            'Git CI input failed: ' + run.stderr.decode(errors='replace').strip())
    return run


def revision(root, value, *, optional=False):
    require(isinstance(value, str) and value and not value.startswith('-'), 'Invalid Git revision')
    run = git(root, 'rev-parse', '--verify', '--end-of-options', value + '^{commit}', check=False)
    if optional and run.returncode:
        return None
    require(run.returncode == 0, 'CI revision is unavailable: ' + value)
    return run.stdout.decode().strip()


@contextmanager
def snapshot(root, commit):
    """Read committed bytes without checking out or executing historical code."""
    archive = git(root, 'archive', '--format=tar', commit).stdout
    with tempfile.TemporaryDirectory(prefix='codecraft-ci-tree-') as folder:
        tree = Path(folder).resolve()
        links = []
        with tarfile.open(fileobj=io.BytesIO(archive), mode='r:') as stream:
            for member in stream:
                require(member.isdir() or member.isfile() or member.issym(), 'Unsupported Git archive member: ' + member.name)
                output = safe_path(tree, member.name, exists=False)
                if member.isdir():
                    output.mkdir(parents=True, exist_ok=True)
                elif member.issym():
                    require(not Path(member.linkname).is_absolute(), 'CI snapshots reject links outside the repository: ' + member.name)
                    links.append((output, member.linkname))
                else:
                    output.parent.mkdir(parents=True, exist_ok=True)
                    output.write_bytes(stream.extractfile(member).read())
                    output.chmod(member.mode & 0o777)
        # Native sdkconfig links are legitimate. Create them only after regular
        # files, then check the complete chain before resolving any source graph.
        for output, target in links:
            require(output.parent.resolve().is_relative_to(tree) and (output.parent/target).resolve().is_relative_to(tree),
                    'CI snapshots reject links outside the repository: ' + str(output.relative_to(tree)))
            output.parent.mkdir(parents=True, exist_ok=True)
            output.symlink_to(target)
        for output, _ in links:
            try:
                resolved = output.resolve(strict=True)
            except (OSError, RuntimeError) as exc:
                require(False, 'Invalid CI snapshot link: ' + str(output.relative_to(tree)) + ': ' + str(exc))
            require(resolved.is_relative_to(tree), 'CI snapshots reject links outside the repository: ' + str(output.relative_to(tree)))
        yield tree


class Inputs:
    """Data-only inventory using the same native roots and SourceGraph as Catalog."""
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.targets = load_group(self.root, 'devices/*/targets/target.json')
        self.platforms = load_group(self.root, 'platforms/*/platform.json')
        require(self.targets and self.platforms, 'CI requires a nonempty Target/Platform inventory')
        self.graphs = {}
        self.files = {}
        self.directories = {}
        for pid, platform in self.platforms.items():
            require(platform.get('schema_version') == 2, f'{pid}: CI requires platform schema 2')
        for tid, target in self.targets.items():
            require(target.get('schema_version') == 3, f'{tid}: CI requires Target schema 3')
            require(target['path'] == f'devices/{target["device"]}/targets', f'{tid}: invalid Target root')
            require(tid == f'{target["platform"]}/{target["device"]}', f'{tid}: invalid Target identity')
            platform = self.platforms[target['platform']]
            graph = SourceGraph(self.root)
            graph.resolve(native_roots(target, platform))
            self.graphs[tid] = graph
            self.files[tid] = graph.files | {(self.root/name).resolve().relative_to(self.root).as_posix() for name in graph.files}
            # Include added/unlisted files under declared directories. A missing
            # explicit input still fails SourceGraph; it is never filtered out.
            directories = {name for name in graph.edges if (self.root/name).is_dir()}
            self.directories[tid] = directories | {(self.root/name).resolve().relative_to(self.root).as_posix() for name in directories}
        self.rows = {row['id']: row for row in matrix(self)['include']}

    def owners(self, path):
        # The compiled CLI owns export/native dispatch. Runtime Device data does
        # not enter the binary cache; changes to these code inputs affect builds.
        if path in {'Cargo.toml', 'Cargo.lock'} or path.startswith(('tools/cli/src/', '.cargo/')) or path == 'tools/cli/Cargo.toml':
            return set(self.targets)
        if path.startswith('platforms/') and path.endswith('.rs'):
            stack = path.split('/')[1]
            return {tid for tid, target in self.targets.items() if target['platform'] == stack}
        return {tid for tid, graph in self.graphs.items()
                if path in self.files[tid] or any(path.startswith(name + '/') for name in self.directories[tid])}


def selection(before, after, changed, *, full_reason=None):
    """Select current Targets from both sides; removed Targets remain reported."""
    selected = {tid: [] for tid in after.targets}
    changes = []
    if full_reason:
        for reasons in selected.values():
            reasons.append({'path': None, 'reason': full_reason})
    else:
        for path in sorted(set(changed)):
            require(isinstance(path, str), 'Changed paths must be strings')
            safe_path(after.root, path, exists=False)
            dependencies = before.owners(path) | after.owners(path)
            reason = host_only(path, before.root, after.root, declared=bool(dependencies))
            owners = set()
            scope = 'static'
            if reason is None:
                owners = dependencies
                if owners:
                    reason, scope = 'declared native input or pipeline dependency', 'native'
                elif path.startswith(('skills/', 'tools/skill_packages/', 'docs/', 'tests/')):
                    reason = 'independent Skill, maintenance, documentation or host-test source'
                elif path == '.github/target-matrix.json' or path.startswith('.github/ISSUE_TEMPLATE/'):
                    reason = 'generated inventory or contribution metadata; static validation checks it'
                else:
                    # Undeclared native files must not disappear from selection.
                    # Use metadata identities, never chip/board-name heuristics.
                    parts = path.split('/')
                    for inventory in (before, after):
                        for tid, target in inventory.targets.items():
                            if path.startswith(target['path'] + '/'):
                                owners.add(tid)
                            if len(parts) > 1 and parts[0] == 'platforms' and parts[1] == target['platform']:
                                owners.add(tid)
                    if owners:
                        reason, scope = 'undeclared native-area change; conservatively select its owner', 'conservative'
                    else:
                        owners = set(after.targets)
                        reason, scope = 'unclassified infrastructure change; conservatively select all Targets', 'conservative'
            current = sorted(owners & after.targets.keys())
            changes.append({'path': path, 'scope': scope, 'reason': reason, 'targets': current})
            for tid in current:
                selected[tid].append({'path': path, 'reason': reason})
        for tid in after.targets.keys() - before.targets.keys():
            selected[tid].append({'path': after.targets[tid]['path'] + '/target.json', 'reason': 'new Target'})
    matrices = {pid: {'include': []} for pid in sorted(after.platforms)}
    targets = {}
    for tid, reasons in sorted(selected.items()):
        targets[tid] = {'selected': bool(reasons), 'reasons': reasons or [
            {'path': None, 'reason': 'no changed native input or build behavior identified'}]}
        if reasons:
            matrices[after.targets[tid]['platform']]['include'].append(after.rows[tid])
    return {'schema_version': 1, 'static': 'required', 'targets': targets, 'matrices': matrices,
            'counts': {pid: len(rows['include']) for pid, rows in matrices.items()},
            'removed_targets': sorted(before.targets.keys() - after.targets.keys()) if before else [],
            'changes': changes}


def plan(root, *, base=None, head='HEAD', full=False, event=None, event_name=None):
    root = Path(root).resolve()
    require(not (root/'project.yaml').exists(), 'CI planning requires the reference repository')
    require(Path(git(root, 'rev-parse', '--show-toplevel').stdout.decode().strip()).resolve() == root,
            'CI root must be the Git repository root')
    head = revision(root, head)
    full_reason = 'explicit full validation' if full else None
    if event is not None:
        require(base is None and not full, 'Choose GitHub event input or explicit base/full mode')
        require(head == revision(root, 'HEAD'), 'Event planning must use the checked-out revision')
        if event_name == 'pull_request':
            base = revision(root, event['pull_request']['base']['sha'])
            source = revision(root, event['pull_request']['head']['sha'])
            for parent in (base, source):
                require(git(root, 'merge-base', '--is-ancestor', parent, head, check=False).returncode == 0,
                        'PR planning requires the tested merge tree to contain both base and head')
        elif event_name == 'push':
            require(revision(root, event['after']) == head, 'Push event does not match the checked-out revision')
            previous = event.get('before', '')
            require(re.fullmatch(r'[0-9a-f]{40,64}', previous), 'Invalid push baseline')
            base = revision(root, previous, optional=True) if set(previous) != {'0'} else None
            if base is None:
                full_reason = 'push baseline unavailable; conservatively validate all Targets'
        elif event_name in {'workflow_dispatch', 'schedule'}:
            full_reason = 'manual or scheduled full validation'
        else:
            require(False, 'Unsupported CI event: ' + str(event_name))
    require(base is not None or full_reason, 'Provide --base, --full or a supported GitHub event')
    base = revision(root, base) if base else None
    with snapshot(root, head) as head_tree:
        after = Inputs(head_tree)
        if full_reason:
            data = selection(None, after, [], full_reason=full_reason)
        else:
            # Disable rename detection so both the deleted and added paths enter
            # their respective dependency graphs, including moved components.
            paths = git(root, 'diff', '--name-only', '--no-renames', '-z', base, head, '--').stdout
            changed = [name.decode('utf-8') for name in paths.split(b'\0') if name]
            with snapshot(root, base) as base_tree:
                data = selection(Inputs(base_tree), after, changed)
    return {**data, 'base': base, 'head': head, 'mode': 'full' if full_reason else 'affected',
            'reason': full_reason or 'compare native dependencies at both committed revisions'}


def summary(data):
    lines = ['## CI impact plan', '', f'Mode: `{data["mode"]}`. {data["reason"]}.', '',
             f'Base: `{data["base"] or "unavailable"}`; tested head: `{data["head"]}`.', '',
             'Static/host validation is required for every run. Selected Targets retain all examples, variants and clean project checks.', '',
             '| Target | Native validation | Reason |', '| --- | --- | --- |']
    for tid, target in data['targets'].items():
        reasons = '; '.join(sorted({row['reason'] for row in target['reasons']}))
        lines.append(f'| `{tid}` | {"selected" if target["selected"] else "skipped"} | {reasons} |')
    if data['removed_targets']:
        lines += ['', 'Removed Targets (no current build): ' + ', '.join(data['removed_targets'])]
    if data['changes']:
        lines += ['', '<details><summary>Changed-path decisions</summary>', '', '| Path | Scope | Reason |', '| --- | --- | --- |']
        for row in data['changes']:
            path = row['path'].replace('|', '&#124;').replace('\n', '\\n').replace('`', '&#96;')
            lines.append(f'| `{path}` | {row["scope"]} | {row["reason"]} |')
        lines += ['', '</details>']
    return '\n'.join(lines) + '\n'


def github_output(path, data):
    # The compact plan is consumed by the fixed aggregate gate. Native matrices
    # and their counts are produced together, not maintained in separate lists.
    compact = {key: data[key] for key in ('schema_version', 'head', 'counts', 'matrices')}
    with Path(path).open('a') as stream:
        stream.write('plan=' + json.dumps(compact, separators=(',', ':')) + '\n')
        for pid, rows in data['matrices'].items():
            key = pid.replace('-', '_')
            require(re.fullmatch(r'[a-z][a-z0-9_]*', key), 'Invalid platform output name')
            stream.write(key + '=' + json.dumps(rows, separators=(',', ':')) + '\n')
            stream.write(key + '_count=' + str(data['counts'][pid]) + '\n')


def check(needs, *, expected_head=None):
    """A skipped/cancelled required matrix must never produce a passing gate."""
    require(isinstance(needs, dict) and isinstance(needs.get('contracts'), dict), 'Missing contracts job result')
    require(isinstance(needs.get('cli'), dict), 'Missing CLI job result')
    cli_state = needs['cli'].get('result')
    checks = [result('ci/cli', 'passed' if cli_state == 'success' else 'failed',
                     '' if cli_state == 'success' else 'CLI build/test job: ' + str(cli_state))]
    state = needs['contracts'].get('result')
    checks.append(result('ci/contracts', 'passed' if state == 'success' else 'failed',
                         '' if state == 'success' else 'Contracts/planning job: ' + str(state)))
    if state != 'success':
        return checks
    outputs = needs['contracts'].get('outputs')
    require(isinstance(outputs, dict) and isinstance(outputs.get('plan'), str), 'Missing CI selection output')
    data = parse_json(outputs['plan'], 'CI selection output')
    require(isinstance(data, dict) and data.get('schema_version') == 1
            and isinstance(data.get('counts'), dict) and data['counts']
            and isinstance(data.get('matrices'), dict), 'Invalid CI selection output')
    require(isinstance(data.get('head'), str) and re.fullmatch(r'[0-9a-f]{40,64}', data['head']), 'Invalid CI head revision')
    require(expected_head is None or data['head'] == expected_head, 'CI plan does not match the checked-out revision')
    require(set(data['counts']) == set(data['matrices']), 'CI matrix/count mismatch')
    require(set(needs) == {'cli', 'contracts', *data['counts']}, 'Missing or unexpected CI platform job')
    identities = set()
    for pid, count in data['counts'].items():
        require(isinstance(pid, str) and isinstance(data['matrices'][pid], dict), 'Invalid CI platform matrix')
        rows = data['matrices'][pid].get('include')
        require(isinstance(rows, list) and isinstance(needs[pid], dict), 'Invalid CI matrix or job result')
        require(type(count) is int and count >= 0 and count == len(rows), 'CI matrix/count mismatch')
        key = pid.replace('-', '_')
        require(outputs.get(key + '_count') == str(count) and isinstance(outputs.get(key), str), 'CI job output/count mismatch')
        require(parse_json(outputs[key], 'CI matrix output') == data['matrices'][pid], 'CI job output/matrix mismatch')
        for row in rows:
            require(isinstance(row, dict) and row.get('platform') == pid and isinstance(row.get('id'), str)
                    and row['id'] not in identities, 'Invalid/duplicate selected Target')
            identities.add(row['id'])
        actual = needs[pid].get('result')
        expected = 'success' if count else 'skipped'
        if actual != expected:
            checks.append(result('ci/' + pid, 'failed', f'{count} selected Targets require {expected}; got {actual}'))
        else:
            checks.append(result('ci/' + pid, 'passed' if count else 'skipped',
                                 f'{count} selected Targets completed' if count else 'No affected native Target selected'))
    return checks


def main(argv, *, root):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    planner = commands.add_parser('plan', help='Select native CI Targets from committed changes')
    planner.add_argument('--base')
    planner.add_argument('--head', default='HEAD')
    planner.add_argument('--full', action='store_true')
    planner.add_argument('--event', type=Path)
    planner.add_argument('--event-name')
    planner.add_argument('--github-output', type=Path)
    planner.add_argument('--summary', type=Path)
    planner.add_argument('--report', type=Path)
    gate = commands.add_parser('check', help='Check all planned jobs, including failures and skips')
    gate.add_argument('--needs-env', required=True, help='Environment variable containing toJSON(needs)')
    gate.add_argument('--summary', type=Path)
    args = parser.parse_args(argv)
    if args.command == 'plan':
        require(bool(args.event) == bool(args.event_name), '--event and --event-name are required together')
        data = plan(root, base=args.base, head=args.head, full=args.full,
                    event=read_json(args.event) if args.event else None, event_name=args.event_name)
        response = {'schema_version': 2, 'ok': True, 'data': data}
        if args.report:
            write_json(args.report, response)
        if args.github_output:
            github_output(args.github_output, data)
        if args.summary:
            with args.summary.open('a') as stream:
                stream.write(summary(data))
    else:
        require(args.needs_env in os.environ, 'Missing CI job-results environment variable')
        checks = check(parse_json(os.environ[args.needs_env], 'CI job results'), expected_head=revision(root, 'HEAD'))
        ok = all(row['status'] in {'passed', 'skipped'} for row in checks)
        response = {'schema_version': 2, 'ok': ok, 'data': {'results': checks, 'device_verification': 'not_run'}}
        if args.summary:
            with args.summary.open('a') as stream:
                stream.write('## CI result\n\n' + '\n'.join(
                    f'- {row["name"]}: **{row["status"]}** {row["reason"]}' for row in checks) + '\n')
    print(json.dumps(response, ensure_ascii=False, indent=2))
    return 0 if response['ok'] else 1
