"""Portable native projects exported from the same graph used for evidence."""
from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

from io_utils import digest, object_digest, read_json, require, result, safe_path, source_files, write_json
from model import Catalog
from runtime import envelope, exit_code, load_adapter, run_target

BUILD_ENTRY = '''#!/usr/bin/env python3
"""Build the native application; --lock accepts reviewed application/toolchain changes."""
from pathlib import Path
import sys
root = Path(__file__).resolve().parent
sys.path.insert(0, str(root/'skills/_shared'))
from project import project_main
raise SystemExit(project_main(root))
'''


def inventory(path, explicit=()):
    files = {str(file.relative_to(path)): digest(file) for file in source_files(path) if file.name != 'codecraft.lock'}
    # A declared prebuilt resource is a source input even when its extension is
    # normally excluded from directory scans (for example a firmware .bin).
    for relative in explicit:
        file = safe_path(path, relative, exists=False)
        if file.is_file():
            files[relative] = digest(file)
    return files


def profile(path):
    data = read_json(path/'project.yaml')
    require(data.get('schema_version') == 2 and data.get('device') and data.get('target') and data.get('example'), 'invalid project profile')
    require(data.get('secrets') == {}, 'Project profile must not contain secret values')
    require(isinstance(data.get('capabilities', []), list), 'Capability selections must be a list')
    if 'variant' in data:
        require(isinstance(data['variant'], str) and data['variant'] and data.get('physical_compatibility') == 'unknown', 'Variant project profile must preserve unresolved physical identity')
    return data


def generate_project(catalog, tid, example, output, capabilities=None, variant=None):
    selected = catalog.selected_target(tid, example, variant)
    graph = catalog.graph(tid, example, variant)
    capabilities = [] if capabilities is None else capabilities
    require(isinstance(capabilities, list), 'Capability selections must be a list')
    for selection in capabilities:
        catalog.cloud().selection(selection, tid)
        graph.resolve(catalog.cloud().graph(selection['provider']).files)
    output = Path(output).expanduser().resolve()
    require(not output.is_relative_to(catalog.root), 'User projects must be outside the reference repository.')
    require(not output.exists(), 'Output must be a new directory.')
    output.mkdir(parents=True)
    try:
        for relative in sorted(graph.files):
            destination = output/relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(safe_path(catalog.root, relative), destination, follow_symlinks=True)
        # An explicit projection by declared example scope, never by file existence.
        write_json(output/selected['path']/'target.json', selected)
        data = {'schema_version': 2, 'device': selected['device'], 'target': tid, 'example': example,
                'toolchain': selected['toolchain'], 'interfaces': [entry['id'] for entry in selected['interfaces']], 'capabilities': capabilities, 'secrets': {}}
        if 'selected_variant' in selected:
            data['variant'] = selected['selected_variant']
            data['physical_compatibility'] = 'unknown'
        write_json(output/'project.yaml', data)
        (output/'build.py').write_text(BUILD_ENTRY)
        from render import paired
        for relative, text in paired('README.md', f'# {selected["device"]}: {example}\n\nActivate the declared toolchain, run `python3 codecraft.py lock-project .` to record the actual environment, then `python3 codecraft.py build-project .`. `python3 codecraft.py verify-project .` checks source integrity. The compatibility commands `python3 build.py --lock` and `python3 build.py` remain available. Builds never flash. After deliberate application edits, review the changes and run `python3 build.py --lock` again. `codecraft.lock` retains the original import provenance and a separate current application snapshot.\n\nproject.yaml uses JSON-compatible YAML 1.2. The native application lives under `{selected["path"]}`. Edit native configuration there; unknown hardware facts remain unknown. A successful build does not verify hardware.\n', f'# {selected["device"]}: {example}\n\n激活声明的工具链，运行 `python3 codecraft.py lock-project .` 记录实际环境，再运行 `python3 codecraft.py build-project .`。`python3 codecraft.py verify-project .` 检查源码完整性。兼容命令 `python3 build.py --lock` 与 `python3 build.py` 仍可使用。构建不会烧录。修改应用后，审查变更并重新运行 `python3 build.py --lock`。`codecraft.lock` 分别保留最初导入来源和当前应用快照。\n\nproject.yaml 使用兼容 JSON 的 YAML 1.2。原生应用位于 `{selected["path"]}`，配置直接在原生文件中修改，未知硬件事实保持 unknown。构建成功不代表硬件验证。\n').items():
            (output/relative).write_text(text)
        if 'variant' in data:
            name=data['variant']
            for relative,note in [('README.md',f'\nSelected build variant: **{name}**. The native default, project profile and lock agree. This choice does not identify the physical panel or PCB revision. Changing assemblies requires the corresponding sourced native inputs and metadata, review and explicit relocking.\n'),
                                  ('README.zh_CN.md',f'\n所选构建变体：**{name}**。原生默认值、项目配置与锁文件一致。该选择不识别实际面板或 PCB 修订；更换组件必须同时引入有来源的原生输入与元数据，审查后明确重新锁定。\n')]:
                (output/relative).write_text((output/relative).read_text()+note)
        (output/'AGENTS.md').write_text('# Application rules\n\nRead README.md and project.yaml. Preserve source citations and native APIs. Keep application changes in this project. Verify/update the lock before building. Device writes require an identified device and explicit authorization; builds and packages never perform them. Keep secrets out of source and locks. Maintain README.md and README.zh_CN.md together; all other engineering documents use English only.\n')
        (output/'.gitignore').write_text('.codecraft/\n__pycache__/\nmanaged_components/\nbuild/\nsdkconfig\nsdkconfig.old\n')
        commit = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=catalog.root, capture_output=True, text=True)
        dirty = subprocess.run(['git', 'status', '--porcelain'], cwd=catalog.root, capture_output=True, text=True)
        origin = {'repository_commit': commit.stdout.strip() if commit.returncode == 0 else 'unknown', 'repository_dirty': bool(dirty.stdout),
                  'target': tid, 'example': example, 'target_source_digest': catalog.graph(tid).fingerprint(),
                  'import_graph': graph.snapshot(), 'import_digest': graph.fingerprint()}
        if 'variant' in data:
            origin['variant'] = data['variant']
        lock = lock_project(output, origin=origin)
        return {'path': str(output), 'target': tid, 'example': example, **({'variant': data['variant']} if 'variant' in data else {}), 'source_digest': lock['source_digest'],
                'origin_source_digest': origin['target_source_digest'], 'toolchain': lock['resolved_toolchain'], 'device_verification': 'not_run'}
    except Exception:
        shutil.rmtree(output)  # Only the fresh directory created by this call.
        raise


def lock_project(path, origin=None):
    path = Path(path).resolve()
    data = profile(path)
    if origin is None:
        previous = read_json(path/'codecraft.lock')
        require(previous.get('schema_version') == 2, 'unsupported lock version')
        origin = previous['origin']
        require(object_digest(origin['import_graph']) == origin['import_digest'], 'original import provenance is corrupt')
    c = Catalog(path)
    target = c.target(data['target'])
    require(target['device'] == data['device'] and target['examples'] == [data['example']], 'profile/Target selection mismatch')
    require(data.get('variant') == target.get('selected_variant'), 'profile/Target variant mismatch')
    for selection in data.get('capabilities', []):
        c.cloud().selection(selection, target['id'])
    adapter = load_adapter(path, c.platforms[target['platform']])
    adapter.validate_target(path, target)
    graph = c.graph(data['target'])
    files = inventory(path, graph.files)
    lock = {'schema_version': 2, 'origin': origin, 'target': data['target'], 'example': data['example'],
            'declared_toolchain': target['toolchain'], 'resolved_toolchain': adapter.probe(path, target),
            'files': files, 'source_digest': object_digest(files), 'dependency_graph': graph.snapshot()}
    if 'variant' in data:
        lock['variant'] = data['variant']
    write_json(path/'codecraft.lock', lock)
    return lock


def verify_project(path):
    path = Path(path).resolve()
    lock = read_json(path/'codecraft.lock')
    require(lock.get('schema_version') == 2 and isinstance(lock.get('files'), dict) and lock['files'], 'invalid project lock')
    require('codecraft.lock' not in lock['files'], 'recursive lock inventory')
    for relative in lock['files']:
        safe_path(path, relative, exists=False)
    require(object_digest(lock['files']) == lock['source_digest'], 'lock digest mismatch')
    require(object_digest(lock['origin']['import_graph']) == lock['origin']['import_digest'], 'import provenance mismatch')
    actual = inventory(path, lock['dependency_graph']['files'])
    drift = sorted(name for name in actual.keys() | lock['files'].keys() if actual.get(name) != lock['files'].get(name))
    data = profile(path)
    require(data['target'] == lock['target'] and data['example'] == lock['example'], 'profile/lock mismatch')
    require(data.get('variant') == lock.get('variant'), 'profile/lock variant mismatch')
    if not drift:
        c = Catalog(path)
        require(data.get('variant') == c.target(data['target']).get('selected_variant'), 'profile/Target variant mismatch')
        require(c.graph(data['target']).snapshot() == lock['dependency_graph'], 'dependency graph differs from lock')
    return {'path': str(path), 'status': 'failed' if drift else 'passed', 'drift': drift, 'source_digest': lock['source_digest']}


def build_project(path):
    path = Path(path).resolve()
    outcome = verify_project(path)
    require(outcome['status'] == 'passed', 'Source changed: review application changes and run python3 build.py --lock.')
    data = profile(path)
    c = Catalog(path)
    target = c.target(data['target'])
    adapter = load_adapter(path, c.platforms[target['platform']])
    actual = adapter.probe(path, target)
    locked = read_json(path/'codecraft.lock')['resolved_toolchain']
    if actual.get('status') != 'passed' or actual != locked:
        checks = [result(name, 'not_run', 'Toolchain is unavailable or differs from codecraft.lock; activate the declared toolchain and explicitly refresh the lock.', actual_toolchain=actual) for name in adapter.cases(path, target, data['example'])]
    else:
        checks = run_target(c, target['id'], data['example'])
    payload = envelope(target['id'], 'build', c.graph(target['id']).fingerprint(), checks)
    payload['project_source_digest'] = outcome['source_digest']
    payload['resolved_toolchain'] = actual
    write_json(path/'.codecraft/build-receipt.json', payload)
    return payload


def package_project(path, output):
    path = Path(path).resolve()
    outcome = verify_project(path)
    require(outcome['status'] == 'passed', 'Project differs from its current lock; review and refresh the lock first.')
    output = Path(output).resolve()
    require(not output.exists() and not output.is_relative_to(path), 'Package output must be new and outside the project.')
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'x', zipfile.ZIP_DEFLATED) as archive:
        for relative in sorted([*read_json(path/'codecraft.lock')['files'], 'codecraft.lock']):
            archive.write(safe_path(path, relative), relative)
    return {'path': str(output), 'sha256': digest(output), 'kind': 'source-package', 'firmware_included': False, 'device_verification': 'not_run'}


def project_main(path):
    import json
    from io_utils import ContractError
    try:
        require(sys.argv[1:] in ([], ['--lock']), 'Usage: python3 build.py [--lock]')
        if '--lock' in sys.argv:
            lock = lock_project(path)
            payload = {'schema_version': 2, 'ok': True, 'operation': 'lock', 'source_digest': lock['source_digest'], 'toolchain': lock['resolved_toolchain']}
        else:
            payload = build_project(path)
        print(json.dumps(payload, ensure_ascii=False))
        return 0 if payload['ok'] else exit_code(payload['results'])
    except (ContractError, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({'schema_version': 2, 'ok': False, 'error': str(exc)}))
        return 1
