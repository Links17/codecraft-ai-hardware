"""Prepare, check and explicitly apply reproducible standalone Skill candidates."""
from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'skills/_shared'))
from graph import SourceGraph
from io_utils import ContractError, digest, object_digest, read_json, require, safe_path, write_json
from registry import domain, load_group


def versions(value):
    require(isinstance(value, str) and re.fullmatch(r'\d+\.\d+\.\d+', value), 'Package version must be major.minor.patch')
    return tuple(map(int, value.split('.')))


def registrations(root):
    providers = load_group(root, 'capabilities/*/providers/*/provider.json')
    providers = {pid:p for pid,p in providers.items() if p['kind']=='repository-skill'}
    require(providers, 'No repository Skill Providers to package')
    require(len({p['skill']['id'] for p in providers.values()})==len(providers), 'A release requires one owning Provider per package')
    for pid,p in providers.items():
        require(pid.count('/')==1 and p['capability']==pid.split('/')[0], 'Invalid Capability/Provider identity')
        require(read_json(safe_path(root,provider_path(p)))==p, 'Provider identity/path mismatch')
        require(p['skill']['path']=='skills/'+p['skill']['id'], 'Invalid package path')
        require(re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', p['skill']['id']), 'Invalid Skill identity')
    return providers


def provider_path(provider):
    return f'capabilities/{provider["capability"]}/providers/{provider["id"].split("/")[1]}/provider.json'


def inputs(root):
    providers = registrations(root)
    graph = SourceGraph(root)
    roots = ['skills/_shared', 'capabilities', 'docs/architecture/capability-provider-policy.md',
             'skills/_cloud/release.py', 'skills/_cloud/check_candidate.py',
             'skills/_cloud/release-checks.json', 'skills/_cloud/device_api.py',
             'skills/_cloud/import.json', 'skills/_cloud/tests/test_protocol.py']
    inventories = {}
    schema = domain(root, 'capabilities')
    helper = 'scripts/device_api.py'
    maintained = digest(safe_path(root, 'skills/_cloud/device_api.py'))
    for pid,p in providers.items():
        package = safe_path(root, p['skill']['path'])
        inventories[pid] = schema.package_inventory(package)
        require(isinstance(p['skill']['files'],dict) and helper in inventories[pid], 'Package lacks its distribution helper or pinned inventory')
        require(inventories[pid][helper] in {p['skill']['files'].get(helper), maintained},
                f'{pid}: distribution helper differs from both its pin and the maintained source; reconcile local edits before preparing a release')
        roots += p['dependencies']
        roots += [p['skill']['path']+'/'+relative for relative in inventories[pid]]
    graph.resolve(roots)
    return graph.snapshot(), inventories, providers


def diff_files(before, after):
    return [{'path':name, 'before':before.get(name), 'after':after.get(name)}
            for name in sorted(before.keys() | after.keys()) if before.get(name)!=after.get(name)]


def copy_verified(source, destination, checksum):
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(source.read_bytes())
    require(digest(destination)==checksum, 'A reviewed file changed while being copied')


def copy_package(source, destination, files):
    """Distribute only pinned bytes, never ignored caches or neighboring files."""
    destination.mkdir()
    for relative,checksum in sorted(files.items()):
        copy_verified(safe_path(source, relative), safe_path(destination, relative, exists=False), checksum)


def proposal(previous, proposed, capability):
    """Validate version/fingerprint changes again when consuming a candidate."""
    expected = copy.deepcopy(previous)
    for key in ('version','api_version','files'):expected['skill'][key]=proposed['skill'][key]
    expected['contract_version']=proposed['contract_version']
    expected['policy']['version']=proposed['policy']['version']
    require(expected==proposed, 'Release cannot rewrite bindings, semantics or provenance')
    changes=diff_files(previous['skill']['files'], proposed['skill']['files'])
    kind='none' if not changes else ('documentation' if all(x['path'].endswith('.md') for x in changes) else 'runtime')
    old_version=versions(previous['skill']['version']);new_version=versions(proposed['skill']['version'])
    require(new_version>=old_version, 'Package version cannot decrease')
    api=proposed['skill']['api_version']
    require(isinstance(api,str) and api.strip(), 'API version must be explicit')
    if changes or api!=previous['skill']['api_version']:
        require(new_version>old_version, previous['id']+': changed package/API needs an explicit higher Skill version')
    require(versions(proposed['policy']['version'])>=versions(previous['policy']['version']), 'Policy version cannot decrease')
    require(proposed['contract_version']==capability['version'], 'Release contract version must match the reviewed Capability')
    return changes,kind


def prepare(root, output, releases=None):
    root = Path(root).resolve();output = Path(output).expanduser().resolve()
    require(not output.exists() and not output.is_relative_to(root), 'Candidate output must be a new directory outside the repository')
    releases = {} if releases is None else releases
    require(isinstance(releases, dict), 'Release versions must be an object keyed by Provider ID')
    sources, inventories, providers = inputs(root)
    require(set(releases)<=providers.keys(), 'Unknown Provider in release versions')
    schema = domain(root, 'capabilities');packages = {};files = {}
    output.mkdir(parents=True)
    try:
        for pid,p in sorted(providers.items()):
            override = releases.get(pid, {})
            require(isinstance(override, dict) and set(override)<=
                    {'skill_version','api_version','contract_version','policy_version'}, 'Unknown release version field')
            proposed = copy.deepcopy(p);skill = proposed['skill'];relative = skill['path']
            package = output/relative;package.mkdir(parents=True)
            require('scripts/device_api.py' in inventories[pid], 'Package lacks its distribution helper')
            for name in inventories[pid]:
                source = root/'skills/_cloud/device_api.py' if name=='scripts/device_api.py' else safe_path(root, relative+'/'+name)
                target = package/name;target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(source.read_bytes())
            skill['files'] = schema.package_inventory(package)
            skill['version'] = override.get('skill_version', skill['version'])
            skill['api_version'] = override.get('api_version', skill['api_version'])
            proposed['contract_version'] = override.get('contract_version', proposed['contract_version'])
            proposed['policy']['version'] = override.get('policy_version', proposed['policy']['version'])
            capability=read_json(root/f'capabilities/{p["capability"]}/capability.json')
            changes,kind=proposal(p,proposed,capability)
            schema.policy(proposed,capability)
            path = provider_path(proposed);write_json(output/path, proposed)
            files[path] = digest(output/path)
            files.update({relative+'/'+name:checksum for name,checksum in skill['files'].items()})
            packages[pid] = {'provider_path':path, 'skill_path':relative, 'classification':kind,
                             'changes':changes, 'previous':p, 'proposed':proposed}
        manifest = {'schema_version':1, 'kind':'skill-release-candidate', 'sources':sources,
                    'baseline_packages':inventories, 'packages':packages, 'files':files,
                    'provenance_sha256':digest(root/'skills/_cloud/import.json')}
        write_json(output/'manifest.json', manifest)
        return {'path':str(output), 'review_sha256':object_digest(manifest),
                'packages':{pid:{'classification':p['classification'],'changes':p['changes']} for pid,p in packages.items()},
                'repository_changed':False, 'api_execution':'not_run', 'published':False}
    except Exception:
        shutil.rmtree(output)  # Only this call's newly created candidate.
        raise


def inspect(root, candidate, reviewed=None):
    root = Path(root).resolve();candidate = Path(candidate).resolve()
    require(not candidate.is_relative_to(root), 'Candidate must be outside the repository')
    manifest = read_json(candidate/'manifest.json');checksum = object_digest(manifest)
    keys={'schema_version','kind','sources','baseline_packages','packages','files','provenance_sha256'}
    require(isinstance(manifest,dict) and set(manifest)==keys and type(manifest['schema_version']) is int
            and manifest['schema_version']==1 and manifest['kind']=='skill-release-candidate', 'Invalid candidate manifest')
    require(all(isinstance(manifest[key],dict) for key in ('sources','baseline_packages','packages','files')), 'Candidate inventories must be objects')
    if reviewed is not None:
        require(isinstance(reviewed, str) and reviewed==checksum, 'Candidate differs from the explicitly reviewed digest')
    schema = domain(root, 'capabilities')
    actual = schema.package_inventory(candidate)
    require(actual=={**manifest['files'], 'manifest.json':digest(candidate/'manifest.json')}, 'Candidate files drifted')
    sources, inventories, providers = inputs(root)
    require(sources==manifest['sources'] and inventories==manifest['baseline_packages'], 'Maintained sources changed after candidate preparation')
    require(set(providers)==set(manifest['packages']), 'Candidate Provider set changed')
    require(digest(root/'skills/_cloud/import.json')==manifest['provenance_sha256'], 'Original import provenance changed')
    for pid,entry in manifest['packages'].items():
        require(entry['previous']==providers[pid], 'Provider changed after candidate preparation')
        proposed = entry['proposed']
        changes,kind=proposal(providers[pid],proposed,read_json(root/f'capabilities/{providers[pid]["capability"]}/capability.json'))
        require(entry['changes']==changes and entry['classification']==kind,'Candidate change summary differs from its bytes')
        require(entry['provider_path']==provider_path(providers[pid]) and entry['skill_path']==providers[pid]['skill']['path'], 'Release cannot relocate a Provider or package')
        require(read_json(safe_path(candidate, entry['provider_path']))==proposed, 'Candidate Provider metadata mismatch')
        require(proposed['source']==providers[pid]['source'], 'Release cannot rewrite original provenance')
        require(schema.package_inventory(safe_path(candidate, entry['skill_path']))==proposed['skill']['files'], 'Candidate package differs from proposed fingerprints')
    return manifest, checksum


def validate(root, candidate, reviewed=None):
    root = Path(root).resolve();candidate = Path(candidate).resolve()
    manifest, checksum = inspect(root, candidate, reviewed)
    with tempfile.TemporaryDirectory(prefix='codecraft-release-check-') as folder:
        staged = Path(folder)
        for relative,expected in manifest['sources']['files'].items():
            copy_verified(safe_path(root, relative), staged/relative, expected)
        for entry in manifest['packages'].values():
            destination = staged/entry['skill_path']
            if destination.exists():shutil.rmtree(destination)
            copy_package(candidate/entry['skill_path'], destination, entry['proposed']['skill']['files'])
            copy_verified(candidate/entry['provider_path'], staged/entry['provider_path'], manifest['files'][entry['provider_path']])
        env = os.environ.copy()
        for name in ('PYTHONPATH','CODECRAFT_API_ORIGIN','CODECRAFT_DEVICE_FILE'):env.pop(name, None)
        run = subprocess.run([sys.executable, '-I', '-B', str(staged/'skills/_cloud/check_candidate.py')],
                             cwd=staged, env=env, capture_output=True, text=True, timeout=180)
        require(run.returncode==0, 'Candidate offline checks failed: '+run.stdout+run.stderr)
        result = json.loads(run.stdout)
        require(result.get('status')=='passed' and result.get('checks') and all(x['status']=='passed' for x in result['checks']), 'Incomplete candidate checks')
    inspect(root, candidate, checksum)  # Source drift during checks is not accepted.
    return {'review_sha256':checksum, **result, 'repository_changed':False, 'api_execution':'not_run', 'published':False}


def apply(root, candidate, reviewed):
    root = Path(root).resolve();candidate = Path(candidate).resolve()
    require(isinstance(reviewed, str) and re.fullmatch(r'[0-9a-f]{64}', reviewed), 'Apply requires an explicitly reviewed candidate digest')
    lock = root/'.codecraft/skill-release.lock';lock.parent.mkdir(parents=True, exist_ok=True)
    try:
        handle = lock.open('x')
    except FileExistsError as exc:
        raise ContractError('Another release owns .codecraft/skill-release.lock; inspect that operation before removing a stale lock') from exc
    try:
        with handle:handle.write(reviewed+'\n')
        checked = validate(root, candidate, reviewed)
        manifest, _ = inspect(root, candidate, reviewed)
        moved = [];written = [];changed = []
        stage = Path(tempfile.mkdtemp(prefix='.release-', dir=root/'skills'))
        clean_stage = False
        try:
            try:
                for pid,entry in sorted(manifest['packages'].items()):
                    destination = root/entry['skill_path'];source = candidate/entry['skill_path']
                    if manifest['baseline_packages'][pid]!=entry['proposed']['skill']['files']:
                        ready = stage/('new-'+destination.name);backup = stage/('old-'+destination.name)
                        copy_package(source, ready, entry['proposed']['skill']['files'])
                        destination.rename(backup);moved.append((destination, backup))
                        ready.rename(destination);changed.append(entry['skill_path'])
                    if entry['previous']!=entry['proposed']:
                        path = root/entry['provider_path'];written.append((path, path.read_bytes()))
                        temporary = stage/(destination.name+'.json')
                        copy_verified(candidate/entry['provider_path'], temporary, manifest['files'][entry['provider_path']])
                        os.replace(temporary, path);changed.append(entry['provider_path'])
                require(digest(root/'skills/_cloud/import.json')==manifest['provenance_sha256'], 'Original provenance changed during apply')
                from model import load_cloud
                load_cloud(root)
            except Exception:
                try:
                    for path,content in reversed(written):path.write_bytes(content)
                    for destination,backup in reversed(moved):
                        if destination.exists():shutil.rmtree(destination)
                        backup.rename(destination)
                except Exception as error:
                    raise ContractError(f'Rollback incomplete; retained recovery files at {stage}') from error
                clean_stage = True
                raise
            clean_stage = True
        finally:
            # If restoring a backup itself fails, retain it for explicit recovery.
            # Never delete the only remaining copy of a pre-existing package.
            if clean_stage:shutil.rmtree(stage)
        return {**checked, 'repository_changed':bool(changed), 'changed':changed,
                'next':'Review the diff, regenerate indexes and run the repository gate.'}
    finally:
        lock.unlink()


def main(argv=None, root=ROOT):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    command = sub.add_parser('prepare');command.add_argument('--output', type=Path, required=True)
    command.add_argument('--versions', type=Path)
    command = sub.add_parser('check');command.add_argument('--candidate', type=Path, required=True)
    command = sub.add_parser('apply');command.add_argument('--candidate', type=Path, required=True)
    command.add_argument('--review-sha256', required=True)
    args = parser.parse_args(argv)
    try:
        if args.command=='prepare':
            releases=read_json(args.versions) if args.versions else {}
            require(isinstance(releases,dict),'Release versions must be an object keyed by Provider ID')
            data=prepare(root,args.output,releases)
        elif args.command=='check':data=validate(root,args.candidate)
        else:data=apply(root,args.candidate,args.review_sha256)
        print(json.dumps({'schema_version':2,'ok':True,'data':data},ensure_ascii=False,indent=2));return 0
    except (ContractError,OSError,ValueError,KeyError,TypeError,subprocess.TimeoutExpired) as exc:
        print(json.dumps({'schema_version':2,'ok':False,'error':{'type':'contract','message':str(exc)}}));return 1


if __name__=='__main__':
    raise SystemExit(main())
