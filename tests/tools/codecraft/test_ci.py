"""CI selection must omit unrelated builds without losing native dependency cases."""
from contextlib import contextmanager
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'tools/codecraft'))
import ci
from io_utils import ContractError, read_json, write_json
from model import Catalog


def put(root, path, text='source\n'):
    out = root/path
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text)


def inventory(root):
    """Five data-only Targets; historical adapter/schema code must never run."""
    for stack in ('esp-idf', 'linux', 'arduino'):
        write_json(root/f'platforms/{stack}/platform.json', {
            'id': stack, 'schema_version': 2, 'adapter': f'platforms/{stack}/adapter.py',
            'runtime': ['tools/codecraft/resource.json'], 'ci': {'runner': 'ubuntu-latest'},
        })
        put(root, f'platforms/{stack}/adapter.py', 'raise AssertionError("historical adapter executed")\n')
    put(root, 'platforms/schema.py', 'raise AssertionError("historical schema executed")\n')
    shared = 'platforms/esp-idf/components/sensor'
    write_json(root/f'{shared}/resource.json', {'schema_version': 1, 'kind': 'resource',
                                               'inputs': [shared + '/sensor.c'], 'dependencies': []})
    put(root, shared + '/sensor.c')
    for stack, board in [('esp-idf','alpha'), ('esp-idf','beta'), ('esp-idf','gamma'),
                         ('linux','delta'), ('arduino','uno')]:
        base = f'devices/{board}/targets'
        write_json(root/base/'target.json', {
            'id': stack + '/' + board, 'schema_version': 3, 'device': board,
            'path': base, 'platform': stack, 'inputs': [base + '/bsp'],
            'dependencies': [shared] if board in {'alpha','beta'} else [],
            'examples': ['demo'], 'example_inputs': {'demo': [base + '/examples/demo']},
            'example_dependencies': {'demo': []}, 'variants': {}, 'interfaces': [],
            'toolchain': {'version': 'fixture', 'source': base + '/README.md'},
        })
        put(root, base + '/bsp/board.c')
        put(root, base + '/examples/demo/main.c')
        put(root, base + '/README.md', '# Native fixture\n')
    write_json(root/'tools/codecraft/resource.json', {'schema_version': 1, 'kind': 'resource',
        'inputs': ['tools/codecraft/maintenance.py', 'tools/codecraft/project.py', 'tools/codecraft/cli.py',
                   'tools/codecraft/io_utils.py'], 'dependencies': []})
    put(root, 'tools/codecraft/maintenance.py', 'raise AssertionError("historical public entry executed")\n')
    put(root, 'tools/codecraft/project.py', 'def build(): return "native"\n')
    for name in ('cli.py', 'io_utils.py'):
        put(root, 'tools/codecraft/' + name, (ROOT/'tools/codecraft'/name).read_text())
    put(root, 'tools/codecraft/ci.py', '# Repository maintenance is present.\n')


@contextmanager
def trees():
    with tempfile.TemporaryDirectory(prefix='codecraft-ci-test-') as folder:
        before, after = Path(folder)/'before', Path(folder)/'after'
        inventory(before)
        shutil.copytree(before, after)
        yield before, after


def selected(before, after, paths):
    data = ci.selection(ci.Inputs(before), ci.Inputs(after), paths)
    return {tid for tid, row in data['targets'].items() if row['selected']}


def reject(fn, text):
    try:
        fn()
    except ContractError as error:
        assert text.lower() in str(error).lower(), str(error)
    else:
        raise AssertionError('Expected rejection: ' + text)


def test_documentation_skill_maintenance_and_host_tests_select_no_native_targets():
    with trees() as (before, after):
        paths = ['AGENTS.md', 'devices/alpha/targets/README.md', 'docs/inventory.json',
                 'skills/sdk/scripts/validate.py', 'tools/skill_packages/sdk/release.py',
                 'tools/codecraft/evidence.py', 'tests/devices/alpha/targets/test_board.c']
        for path in paths:
            put(after, path)
        assert selected(before, after, paths) == set()


def test_board_source_example_and_variant_inputs_select_only_their_target():
    with trees() as (before, after):
        for path in ['devices/alpha/targets/bsp/board.c', 'devices/alpha/targets/examples/demo/main.c',
                     'devices/alpha/targets/bsp/new.c', 'devices/alpha/targets/examples/demo/prompt.md']:
            put(after, path, 'changed\n')
            assert selected(before, after, [path]) == {'esp-idf/alpha'}
        path = 'devices/alpha/targets/target.json'
        target = read_json(after/path)
        target['variants'] = {'panel': {'inputs': ['devices/alpha/assets/panel.bin'], 'dependencies': []}}
        put(after, 'devices/alpha/assets/panel.bin')
        write_json(after/path, target)
        assert selected(before, after, ['devices/alpha/assets/panel.bin']) == {'esp-idf/alpha'}


def test_shared_component_selects_consumers_including_unlisted_directory_additions():
    with trees() as (before, after):
        for path in ['platforms/esp-idf/components/sensor/sensor.c',
                     'platforms/esp-idf/components/sensor/extra.c']:
            put(after, path)
            assert selected(before, after, [path]) == {'esp-idf/alpha', 'esp-idf/beta'}


def test_platform_and_shared_native_pipeline_have_the_correct_blast_radius():
    with trees() as (before, after):
        assert selected(before, after, ['platforms/esp-idf/adapter.py']) == {
            'esp-idf/alpha', 'esp-idf/beta', 'esp-idf/gamma'}
        assert selected(before, after, ['tools/codecraft/project.py']) == set(ci.Inputs(after).targets)
        assert selected(before, after, ['tools/codecraft/render.py']) == set(ci.Inputs(after).targets)
        assert selected(before, after, ['platforms/esp-idf/new-build-helper.py']) == {
            'esp-idf/alpha', 'esp-idf/beta', 'esp-idf/gamma'}


def test_removed_dependencies_and_renames_use_both_trees():
    with trees() as (before, after):
        old = 'platforms/esp-idf/components/sensor/sensor.c'
        for board in ('alpha', 'beta'):
            path = after/f'devices/{board}/targets/target.json'
            target = read_json(path)
            target['dependencies'] = []
            write_json(path, target)
        shutil.rmtree(after/'platforms/esp-idf/components/sensor')
        assert selected(before, after, [old]) == {'esp-idf/alpha', 'esp-idf/beta'}
        new = 'devices/gamma/targets/bsp/moved.c'
        put(after, new)
        assert selected(before, after, [old, new]) == {'esp-idf/alpha', 'esp-idf/beta', 'esp-idf/gamma'}


def test_removed_target_is_reported_and_new_target_is_selected():
    with trees() as (before, after):
        shutil.rmtree(after/'devices/alpha')
        shutil.copytree(after/'devices/gamma', after/'devices/new-board')
        path = after/'devices/new-board/targets/target.json'
        path.write_text(path.read_text().replace('gamma', 'new-board'))
        data = ci.selection(ci.Inputs(before), ci.Inputs(after), ['devices/alpha/targets/target.json'])
        assert data['removed_targets'] == ['esp-idf/alpha']
        assert 'esp-idf/alpha' not in data['targets']
        assert data['targets']['esp-idf/new-board']['selected']
        assert not data['targets']['esp-idf/gamma']['selected']


def test_missing_and_cyclic_native_inputs_fail_instead_of_being_filtered():
    with trees() as (before, after):
        (after/'devices/alpha/targets/bsp/board.c').unlink()
        reject(lambda: ci.Inputs(after), 'empty dependency directory')
        put(after, 'devices/alpha/targets/bsp/board.c')
        path = after/'platforms/esp-idf/components/sensor/resource.json'
        resource = read_json(path)
        resource['dependencies'] = ['platforms/esp-idf/components/sensor']
        write_json(path, resource)
        reject(lambda: ci.Inputs(after), 'dependency cycle')


def test_unknown_infrastructure_change_expands_instead_of_silently_skipping():
    with trees() as (before, after):
        for path in ('.github/workflows/hardware.yml', 'new-build-driver.sh'):
            data = ci.selection(ci.Inputs(before), ci.Inputs(after), [path])
            assert all(row['selected'] for row in data['targets'].values())
            assert data['changes'][0]['scope'] == 'conservative'


def test_host_cli_and_package_inventory_changes_do_not_trigger_native_builds():
    with trees() as (before, after):
        path = 'tools/codecraft/cli.py'
        source = (after/path).read_text()
        # The literal host guard is unreachable for native commands.
        source = source.replace("if args.command=='skill-reference':", "if args.command=='skill-reference':\n            print('host-only maintenance')")
        put(after, path, source)
        assert selected(before, after, [path]) == set()
        path = 'tools/codecraft/io_utils.py'
        source = (after/path).read_text().replace('def package_inventory(package):',
                                                'def package_inventory(package):\n    print("inventory maintenance")')
        put(after, path, source)
        assert selected(before, after, [path]) == set()


def test_native_cli_changes_and_parser_side_effects_remain_native_impact():
    with trees() as (before, after):
        path = 'tools/codecraft/cli.py'
        original = (before/path).read_text()
        for source in (
            original.replace('checks=run_target(c,args.target,args.example,args.variant)',
                             'checks=run_target(c,args.target,None,args.variant)'),
            original.replace("reference.add_argument('--revision')", "reference.add_argument('--revision',default=mutate_native_inputs())"),
            original.replace("reference=sub.add_parser('skill-reference',", "reference=sub.add_parser('skill-reference',parents=mutate_native_inputs(),"),
            original.replace("if args.command=='skill-reference':", "if mutate_native_inputs() and args.command=='skill-reference':"),
            original.replace("ci=sub.add_parser('ci',", "run_target=sub.add_parser('ci',")
                    .replace("ci.add_argument('ci_args',", "run_target.add_argument('ci_args',"),
        ):
            assert source != original
            put(after, path, source)
            assert selected(before, after, [path]) == set(ci.Inputs(after).targets)
        path = 'tools/codecraft/io_utils.py'
        put(after, path, (before/path).read_text().replace('if exists:', 'if not exists:'))
        assert selected(before, after, [path]) == set(ci.Inputs(after).targets)


def commit(root):
    ci.git(root, 'add', '--all')
    ci.git(root, '-c', 'user.name=CI Fixture', '-c', 'user.email=ci@example.invalid',
           '-c', 'commit.gpgsign=false', '-c', 'core.hooksPath=/dev/null', 'commit', '-qm', 'fixture')
    return ci.revision(root, 'HEAD')


def test_git_and_github_event_plans_use_tested_revisions_and_safe_full_fallbacks():
    with trees() as (_, root):
        ci.git(root, 'init', '-q')
        base = commit(root)
        put(root, 'devices/delta/targets/examples/demo/main.c', 'new native input\n')
        head = commit(root)
        data = ci.plan(root, base=base)
        assert data['base'] == base and data['head'] == head
        assert data['counts'] == {'arduino': 0, 'esp-idf': 0, 'linux': 1}
        event = {'pull_request': {'base': {'sha': base}, 'head': {'sha': head}}}
        assert ci.plan(root, event=event, event_name='pull_request')['counts'] == data['counts']
        assert ci.plan(root, event={'before': base, 'after': head}, event_name='push')['counts'] == data['counts']
        for previous in ('0' * 40, 'f' * 40):
            fallback = ci.plan(root, event={'before': previous, 'after': head}, event_name='push')
            assert fallback['mode'] == 'full' and sum(fallback['counts'].values()) == 5
        assert sum(ci.plan(root, full=True)['counts'].values()) == 5
        assert sum(ci.plan(root, event={}, event_name='workflow_dispatch')['counts'].values()) == 5
        reject(lambda: ci.plan(root, base='missing-ref'), 'unavailable')
        reject(lambda: ci.plan(root, event={'before': base, 'after': base}, event_name='push'), 'does not match')
        put(root, 'README.md', '# Docs only\n')
        docs = commit(root)
        assert sum(ci.plan(root, base=head, head=docs)['counts'].values()) == 0
        # Uncommitted changes are not silently presented as validated commits.
        put(root, 'devices/alpha/targets/bsp/board.c', 'dirty\n')
        assert sum(ci.plan(root, base=head, head=docs)['counts'].values()) == 0


def test_git_snapshots_reject_links_and_do_not_execute_historical_python():
    with trees() as (_, root):
        ci.git(root, 'init', '-q')
        base = commit(root)
        assert ci.plan(root, base=base)['counts'] == {'arduino': 0, 'esp-idf': 0, 'linux': 0}
        (root/'escape').symlink_to('/etc/passwd')
        commit(root)
        reject(lambda: ci.plan(root, full=True), 'reject links')


def test_internal_config_links_preserve_dependency_ownership():
    with trees() as (_, root):
        put(root, 'common-native-config', 'original\n')
        link = root/'devices/alpha/targets/bsp/sdkconfig.defaults'
        link.symlink_to(os.path.relpath(root/'common-native-config', link.parent))
        ci.git(root, 'init', '-q')
        base = commit(root)
        put(root, 'common-native-config', 'changed\n')
        commit(root)
        data = ci.plan(root, base=base)
        assert {tid for tid, row in data['targets'].items() if row['selected']} == {'esp-idf/alpha'}


def needs_for(data):
    compact = {key: data[key] for key in ('schema_version', 'counts', 'matrices')}
    compact['head'] = data.get('head', 'a' * 40)
    outputs = {'plan': json.dumps(compact)}
    for pid, count in data['counts'].items():
        outputs[pid.replace('-', '_') + '_count'] = str(count)
        outputs[pid.replace('-', '_')] = json.dumps(data['matrices'][pid])
    return {'cli': {'result': 'success'}, 'contracts': {'result': 'success', 'outputs': outputs},
            **{pid: {'result': 'success' if count else 'skipped'} for pid, count in data['counts'].items()}}


def test_aggregate_gate_requires_selected_jobs_and_reports_planned_skips():
    with trees() as (before, after):
        data = ci.selection(ci.Inputs(before), ci.Inputs(after), ['devices/delta/targets/bsp/board.c'])
        needs = needs_for(data)
        rows = ci.check(needs)
        assert {row['name']: row['status'] for row in rows} == {
            'ci/cli': 'passed', 'ci/contracts': 'passed', 'ci/arduino': 'skipped', 'ci/esp-idf': 'skipped', 'ci/linux': 'passed'}
        for state in ('failure', 'cancelled', 'skipped', None):
            broken = copy.deepcopy(needs)
            broken['linux']['result'] = state
            assert any(row['status'] == 'failed' for row in ci.check(broken))
        broken = copy.deepcopy(needs)
        broken['contracts'] = {'result': 'failure'}
        assert any(row['name'] == 'ci/contracts' and row['status'] == 'failed' for row in ci.check(broken))
        broken = copy.deepcopy(needs)
        del broken['linux']
        reject(lambda: ci.check(broken), 'Missing or unexpected')
        broken = copy.deepcopy(needs)
        plan = json.loads(broken['contracts']['outputs']['plan'])
        plan['counts']['linux'] = 0
        broken['contracts']['outputs']['plan'] = json.dumps(plan)
        reject(lambda: ci.check(broken), 'matrix/count mismatch')
        reject(lambda: ci.check(needs, expected_head='b' * 40), 'checked-out revision')
        broken = copy.deepcopy(needs)
        broken['contracts']['outputs']['linux'] = '{"include": []}'
        reject(lambda: ci.check(broken), 'output/matrix mismatch')
        for malformed in ('null', '[]', '{}'):
            broken['contracts']['outputs']['plan'] = malformed
            reject(lambda: ci.check(broken), 'Invalid CI selection output')


def test_public_ci_commands_emit_json_github_outputs_and_summary():
    with trees() as (_, root), tempfile.TemporaryDirectory() as folder:
        ci.git(root, 'init', '-q')
        base = commit(root)
        report, output, summary = [Path(folder)/name for name in ('plan.json', 'output.txt', 'summary.md')]
        run = subprocess.run([sys.executable, str(ROOT/'tools/codecraft/maintenance.py'), '--root', str(root), 'ci', 'plan',
                              '--base', base, '--report', str(report), '--github-output', str(output),
                              '--summary', str(summary)], capture_output=True, text=True, timeout=30)
        assert run.returncode == 0, run.stdout + run.stderr
        payload = json.loads(run.stdout)
        assert payload == read_json(report) and payload['schema_version'] == 2 and payload['ok']
        outputs = dict(line.split('=', 1) for line in output.read_text().splitlines())
        assert outputs['esp_idf_count'] == outputs['linux_count'] == outputs['arduino_count'] == '0'
        assert json.loads(outputs['esp_idf']) == {'include': []}
        assert 'skipped' in summary.read_text()
        needs = needs_for(payload['data'])
        env = {**os.environ, 'CODECRAFT_CI_TEST_NEEDS': json.dumps(needs)}
        command = [sys.executable, str(ROOT/'tools/codecraft/maintenance.py'), '--root', str(root), 'ci', 'check', '--needs-env', 'CODECRAFT_CI_TEST_NEEDS']
        run = subprocess.run(command, env=env, capture_output=True, text=True, timeout=30)
        assert run.returncode == 0 and json.loads(run.stdout)['ok']
        needs['contracts']['result'] = 'cancelled'
        env['CODECRAFT_CI_TEST_NEEDS'] = json.dumps(needs)
        run = subprocess.run(command, env=env, capture_output=True, text=True, timeout=30)
        assert run.returncode == 1 and not json.loads(run.stdout)['ok']


def test_real_target_dependency_projection_preserves_all_native_source_closure():
    catalog = Catalog(ROOT)
    inventory = ci.Inputs(ROOT)
    assert inventory.rows == {row['id']: row for row in ci.matrix(catalog)['include']}
    for tid, target in catalog.targets.items():
        files = inventory.graphs[tid].files
        assert files <= catalog.graph(tid).files
        assert target['path'] + '/target.json' in files
        assert catalog.platforms[target['platform']]['adapter'] in files
        assert 'tools/codecraft/maintenance.py' in files


def test_workflow_keeps_static_gate_native_commands_and_a_fixed_aggregate_job():
    source = (ROOT/'.github/workflows/hardware.yml').read_text()
    assert 'fetch-depth: 0' in source and '.codecraft/bin/codecraft validate --static' in source
    assert '--event "$GITHUB_EVENT_PATH" --event-name "$GITHUB_EVENT_NAME"' in source
    assert 'paths-ignore:' not in source and 'continue-on-error:' not in source
    assert 'if: always()' in source and 'needs: [cli, contracts, esp-idf, linux, arduino]' in source
    assert "github.event_name == 'pull_request' && github.ref || github.run_id" in source
    assert "cancel-in-progress: ${{ github.event_name == 'pull_request' }}" in source
    assert 'CODECRAFT_CI_NEEDS: ${{ toJSON(needs) }}' in source
    for key in ('esp_idf', 'linux', 'arduino'):
        assert f"if: needs.contracts.outputs.{key}_count != '' && needs.contracts.outputs.{key}_count != '0'" in source
        assert f'matrix: ${{{{ fromJSON(needs.contracts.outputs.{key}) }}}}' in source
        assert f'{key}: ${{{{ steps.plan.outputs.{key} }}}}' in source
    assert 'command: .codecraft/bin/codecraft validate --target ${{ matrix.id }} --projects' in source
    assert source.count('run: .codecraft/bin/codecraft validate --target "$TARGET" --projects') == 2


def test_rust_native_owners_and_cli_failure_are_required():
    with trees() as (before, after):
        inventory = ci.Inputs(after)
        assert inventory.owners('tools/cli/src/project.rs') == set(inventory.targets)
        assert inventory.owners('platforms/esp-idf/native.rs') == {tid for tid, t in inventory.targets.items() if t['platform'] == 'esp-idf'}
        assert not inventory.owners('docs/development/rust-cli.md')
        data = ci.selection(ci.Inputs(before), inventory, [])
        needs = needs_for(data)
        for state in ('failure', 'cancelled', 'skipped'):
            needs['cli']['result'] = state
            assert any(row['name'] == 'ci/cli' and row['status'] == 'failed' for row in ci.check(needs))
