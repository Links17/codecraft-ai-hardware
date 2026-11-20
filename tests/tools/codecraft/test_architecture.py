"""Source closure, native contracts, project integrity and evidence boundaries."""
from contextlib import contextmanager
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'tools/codecraft'))
from io_utils import ContractError, digest, object_digest, read_json, source_files, write_json
from model import Catalog
import skill_contracts as contracts
from graph import SourceGraph
from project import generate_project, lock_project, verify_project, package_project
from runtime import check_envelope, envelope, load_adapter
from evidence import validate_evidence
from render import generate
from device_entry import read_contract, write_contract


@contextmanager
def fixture():
    with tempfile.TemporaryDirectory(prefix='codecraft-architecture-test-') as folder:
        root = Path(folder)/'repo'
        root.mkdir()
        for source in source_files(ROOT, excluded_dirs={'projects'}):
            out = root/source.relative_to(ROOT)
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, out, follow_symlinks=True)
        yield root


def rejected(fn, fragment):
    try:
        fn()
    except ContractError as exc:
        assert fragment.lower() in str(exc).lower(), str(exc)
    else:
        raise AssertionError('Expected rejection: '+fragment)


def edit(root, path, fn):
    source = root/path
    data = read_contract(source) if source.name == 'AGENTS.md' else read_json(source)
    fn(data)
    (write_contract if source.name == 'AGENTS.md' else write_json)(source, data)


def test_native_adapter_is_part_of_context_export_and_evidence_identity():
    with fixture() as root:
        c = Catalog(root)
        tid = 'esp-idf/reterminal-e1001'
        before = c.graph(tid).fingerprint()
        path = root/'platforms/esp-idf/adapter.py'
        assert str(path.relative_to(root)) in c.context(tid, 'epd_hello')['files']
        path.write_text(path.read_text()+'\n# Changed actual native build entry\n')
        after = Catalog(root).graph(tid).fingerprint()
        assert before != after
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)/'app'
            generate_project(Catalog(root), tid, 'epd_hello', output)
            assert digest(output/'platforms/esp-idf/adapter.py') == digest(path)


def test_transitive_cross_layer_dependency_is_exported_never_filtered():
    with fixture() as root:
        tid = 'esp-idf/reterminal-e1001'
        resource = 'platforms/esp-idf/fixtures/resource.json'
        leaf = 'platforms/esp-idf/fixtures/palette.bin'
        write_json(root/resource, {'schema_version':1,'kind':'resource','inputs':[leaf],'dependencies':[]})
        (root/leaf).write_text('test-only native resource\n')
        edit(root, 'devices/reterminal-e1001/targets/target.json', lambda target: target['dependencies'].append(resource))
        c = Catalog(root)
        assert leaf in c.graph(tid).files
        before = c.graph(tid).fingerprint()
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)/'app'
            generate_project(c, tid, 'epd_hello', output)
            imported = read_json(output/'devices/reterminal-e1001/targets/target.json')
            assert resource in imported['dependencies'] and (output/leaf).is_file()
            assert verify_project(output)['status'] == 'passed'
            package_project(output, Path(folder)/'source.zip')
            import zipfile
            with zipfile.ZipFile(Path(folder)/'source.zip') as archive:
                assert leaf in archive.namelist()
            (output/leaf).unlink()
            assert verify_project(output)['status'] == 'failed'
        (root/leaf).write_text('changed dependent resource\n')
        assert before != Catalog(root).graph(tid).fingerprint()
        (root/leaf).unlink()
        rejected(lambda: Catalog(root), 'missing reference')


def test_cycle_and_external_symlink_dependencies_are_rejected():
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        write_json(root/'a/resource.json',{'schema_version':1,'kind':'resource','inputs':['b/resource.json'],'dependencies':[]})
        write_json(root/'b/resource.json',{'schema_version':1,'kind':'resource','inputs':['a/resource.json'],'dependencies':[]})
        rejected(lambda: SourceGraph(root).resolve(['a']), 'dependency cycle')
        (root/'escape').symlink_to('/etc/passwd')
        rejected(lambda: SourceGraph(root).resolve(['escape']), 'escapes repository')


def test_peripherals_are_target_interfaces_separate_from_cloud_skills():
    c=Catalog(ROOT)
    assert all(target['interfaces'] for target in c.targets.values())
    assert set(contracts.registrations(ROOT))=={'codecraft-capabilities-asr','codecraft-capabilities-llm','codecraft-capabilities-tts','codecraft-capabilities-image-generation'}
    with fixture() as root:
        edit(root,'devices/reterminal-e1001/targets/target.json',lambda target:target.update(skills=['display']))
        rejected(lambda:Catalog(root),'unknown Target')


def test_native_parameter_types_and_resource_limits_remain_explicit():
    c = Catalog(ROOT)
    interface = copy.deepcopy(next(item for item in c.target('esp-idf/reterminal-e1001')['interfaces'] if item['id']=='display'))
    assert c.platform_schema.match_interface(interface,{'configuration':{'width':800}})['status']=='match'
    assert c.platform_schema.match_interface(interface,{'configuration':{'width':100}})['status']=='unsupported'
    assert c.platform_schema.match_interface(interface,{'resources':{'peak_memory_bytes':64000}})['status']=='unknown'
    interface['resources']['peak_memory_bytes'].update(status='known',value=48000)
    assert c.platform_schema.match_interface(interface,{'resources':{'peak_memory_bytes':64000}})['status']=='match'
    assert c.platform_schema.match_interface(interface,{'resources':{'peak_memory_bytes':32000}})['status']=='unsupported'
    rejected(lambda:c.platform_schema.match_interface(interface,{'configuration':{'width':'wrong type'}}),'type mismatch')


def test_numeric_facts_cannot_contradict_their_source_or_declared_type():
    with fixture() as root:
        path = 'devices/reterminal-e1001/AGENTS.md'
        original = read_contract(root/path)
        edit(root,path,lambda device:device['facts']['flash'].update(value=64))
        rejected(lambda: Catalog(root),'contradicts cited source')
        write_contract(root/path,original)
        changed=copy.deepcopy(original);changed['facts']['flash']['value']='sixty-four'
        rejected(lambda:write_contract(root/path,changed) or Catalog(root),'invalid integer')
        write_contract(root/path,original)
        changed=copy.deepcopy(original);changed['specs']={'Controller':'64 MB'}
        rejected(lambda:write_contract(root/path,changed),'unsupported Device fields')


def test_device_target_backlinks_cannot_be_registered_twice():
    with fixture() as root:
        rejected(lambda:edit(root,'devices/reterminal/AGENTS.md',lambda device:device.update(targets=['linux/reterminal'])),
                 'unsupported Device fields')


def test_context_and_import_choose_declared_example_scope():
    c = Catalog(ROOT)
    context = c.context('linux/reterminal','buttons_evdev',task='build')
    assert 'skills/codecraft-development-build/SKILL.md' in context['guidance']
    assert 'skills/codecraft-development-device-test/SKILL.md' not in context['guidance']
    assert all(not path.endswith('/sensors_sysfs.py') for path in context['files'])
    assert 'platforms/esp-idf/components/sscma_client/camera.c' not in c.graph('esp-idf/reterminal-e1001').files
    assert 'platforms/esp-idf/components/sscma_client/camera.c' in c.graph('esp-idf/sensecap-watcher').files


def test_protocol_rejects_wrong_source_identity_partial_or_duplicate_cases():
    cases = [{'name':'native/a','status':'passed','reason':''},{'name':'native/b','status':'passed','reason':''}]
    original = envelope('native/device','build','a'*64,cases)
    for changed in [dict(original,target='wrong'),dict(original,operation='flash'),dict(original,source_digest='b'*64),dict(original,results=cases[:1]),dict(original,results=[cases[0],cases[0]])]:
        rejected(lambda: check_envelope(changed,'native/device','build','a'*64,['native/a','native/b'],0),'adapter')
    rejected(lambda:check_envelope(original,'native/device','build','a'*64,['native/a','native/b'],1),'exit/status')


def test_project_edits_have_explicit_relocking_without_losing_origin():
    with tempfile.TemporaryDirectory() as folder:
        output = Path(folder)/'app'
        generate_project(Catalog(ROOT),'linux/reterminal','buttons_evdev',output)
        original = read_json(output/'codecraft.lock')['origin']
        native = output/'devices/reterminal/targets/demos/buttons_evdev.py'
        native.write_text(native.read_text()+'\n# Deliberate application edit\n')
        assert verify_project(output)['status'] == 'failed'
        lock_project(output)
        assert verify_project(output)['status'] == 'passed'
        assert read_json(output/'codecraft.lock')['origin'] == original
        outcome = package_project(output,Path(folder)/'app.zip')
        assert outcome['kind'] == 'source-package' and not outcome['firmware_included']


def test_lock_checks_actual_toolchain_before_any_build():
    with tempfile.TemporaryDirectory() as folder:
        output = Path(folder)/'app'
        generate_project(Catalog(ROOT),'linux/reterminal','buttons_evdev',output)
        edit(output,'codecraft.lock',lambda lock:lock.update(resolved_toolchain={'status':'passed','python':'different'}))
        run = subprocess.run([sys.executable,str(output/'codecraft.py'),'build-project',str(output)],capture_output=True,text=True)
        payload = json.loads(run.stdout)['data']
        assert run.returncode == 2 and all(item['status']=='not_run' for item in payload['results'])
        assert not (output/'.codecraft/builds').exists()


def make_build_evidence(c, tid):
    target = c.target(tid)
    path = f'tests/devices/{target["device"]}/logs/synthetic.log'
    (c.root/path).parent.mkdir(parents=True, exist_ok=True)
    (c.root/path).write_text('Synthetic unit-test observation; no real device or build claim.\n')
    adapter = load_adapter(c.root,c.platforms[target['platform']])
    cases = [{'name':name,'status':'passed','toolchain':'synthetic fixture'} for name in adapter.cases(c.root,target)]
    exported_cases = set(adapter.cases(c.root,target,target['examples'][0]))
    source = c.graph(tid).fingerprint()
    return {'schema_version':2,'target':tid,'kind':'build','repository_commit':'0'*40,'repository_dirty':True,
            'source_digest':source,'revision':'unknown','toolchain':'synthetic fixture','command':['test-fixture'],
            'environment':'isolated test','result':'passed','limitations':['Synthetic unit test only'],
            'operator':'test','log':path,'log_sha256':digest(c.root/path),'executed_at':'2026-01-01T00:00:00+00:00','cases':cases,
            'generated_project':{'status':'passed','provenance':'passed','example':target['examples'][0],
                                 'origin_source_digest':source,'source_digest':'a'*64,'build_results':copy.deepcopy([case for case in cases if case['name'] in exported_cases]),'log':path,'log_sha256':digest(c.root/path)}}


def test_evidence_requires_all_native_cases_and_export_from_identical_sources():
    with fixture() as root:
        c = Catalog(root);tid = 'linux/reterminal'
        record = make_build_evidence(c,tid)
        validate_evidence(c,record,current=True)
        record['cases'].pop()
        rejected(lambda:validate_evidence(c,record,current=True),'every native case')
        record = make_build_evidence(c,tid)
        record['generated_project']['origin_source_digest'] = 'b'*64
        rejected(lambda:validate_evidence(c,record,current=True),'same sources')


def test_generated_project_evidence_rejects_omitted_duplicate_and_unselected_cases():
    with fixture() as root:
        c = Catalog(root)
        original = make_build_evidence(c, 'linux/reterminal')
        for mutation in ('omitted-overlay', 'duplicate', 'wrong-example'):
            record = copy.deepcopy(original)
            checks = record['generated_project']['build_results']
            if mutation == 'omitted-overlay':
                checks.pop()
            elif mutation == 'duplicate':
                checks.append(copy.deepcopy(checks[0]))
            else:
                checks[0]['name'] = 'linux/reterminal/sensors_sysfs'
            rejected(lambda: validate_evidence(c, record, current=True), 'every selected native case')


def test_evidence_rejects_unsupported_versions_before_interpreting_observations():
    with fixture() as root:
        c = Catalog(root)
        record = make_build_evidence(c, 'linux/reterminal')
        for version in (1, 3, None):
            record['schema_version'] = version
            rejected(lambda: validate_evidence(c, record), 'Unsupported evidence schema')


def test_adapter_or_contract_changes_invalidate_evidence_but_log_additions_do_not():
    with fixture() as root:
        c = Catalog(root);tid = 'linux/reterminal'
        record = make_build_evidence(c,tid)
        directory = root/'tests/devices/reterminal/records'
        if directory.exists():shutil.rmtree(directory)
        directory.mkdir(parents=True)
        write_json(directory/'fixture.json',record)
        assert Catalog(root).support(tid)['level'] == 'build-verified'
        (root/'tests/devices/reterminal/logs/unrelated.log').write_text('another observation')
        assert Catalog(root).support(tid)['level'] == 'build-verified'
        path = root/'platforms/linux/adapter.py'
        path.write_text(path.read_text()+'\n# Changed actual adapter\n')
        assert Catalog(root).support(tid)['level'] == 'unknown'
        assert Catalog(root).support(tid)['stale_records']


def test_physical_verification_requires_revision_and_complete_named_cases():
    with fixture() as root:
        tid = 'linux/reterminal'
        edit(root,'devices/reterminal/AGENTS.md',lambda device:device.update(revision='synthetic-revision'))
        c=Catalog(root);record=make_build_evidence(c,tid)
        directory=root/'tests/devices/reterminal/records'
        if directory.exists():shutil.rmtree(directory)
        directory.mkdir(parents=True)
        write_json(directory/'build.json',record)
        record.update(kind='device',revision='synthetic-revision',cases=[{'name':'identity','status':'passed','observation':'synthetic identity only','procedure':'test fixture'}])
        write_json(directory/'physical.json',record)
        assert Catalog(root).support(tid)['level']=='build-verified'
        assert Catalog(root).support(tid)['device']=='not_run'
        acceptance=read_contract(root/'devices/reterminal/AGENTS.md')['acceptance']
        record['cases']=[{'name':case['id'],'status':'passed','observation':'synthetic unit-test observation','procedure':'synthetic unit-test procedure'} for case in acceptance['cases']]
        write_json(directory/'physical.json',record)
        assert Catalog(root).support(tid)['level']=='device-verified'
        record['revision']='unknown'
        rejected(lambda:validate_evidence(c,record),'observed revision')


def test_explicit_skill_projection_exports_only_the_selected_package():
    c=Catalog(ROOT);choice=cloud_choice()
    with tempfile.TemporaryDirectory() as folder:
        output=Path(folder)/'project'
        generate_project(c,'linux/reterminal','buttons_evdev',output,[choice])
        assert verify_project(output)['status']=='passed'
        assert read_json(output/'project.yaml')['skills']==[choice]
        assert (output/contracts.record_path('codecraft-capabilities-asr')).is_file()
        assert not (output/'skills/codecraft-capabilities-tts').exists()
        package=output/'skills/codecraft-capabilities-asr'
        assert (package/'scripts/device_api.py').is_file() and (package/'contract.json').is_file()
        lock=read_json(output/'codecraft.lock')
        assert contracts.record_path('codecraft-capabilities-asr') in lock['files']
        assert all(not Path(path).is_absolute() for path in lock['files'])
        assert contracts.selection(output,choice)['execution']=='not_run'
        # Standalone scripts need their own script directory; -E/-s isolates environment without suppressing it.
        run=subprocess.run([sys.executable,'-E','-s','-B',str(package/'scripts/transcribe.py'),'--help'],cwd=folder,capture_output=True,text=True)
        assert run.returncode==0 and '--file' in run.stdout
        (package/'scripts/device_api.py').write_text('# Unreviewed client edit\n')
        assert verify_project(output)['status']=='failed'


def test_package_mutations_missing_pins_and_provenance_are_rejected():
    with fixture() as root:
        path=root/'skills/codecraft-capabilities-asr/scripts/transcribe.py'
        path.write_text(path.read_text()+'\n# Unreviewed runtime change\n')
        rejected(lambda:contracts.load_package(root,'codecraft-capabilities-asr'),'reviewed release')
    with fixture() as root:
        edit(root,contracts.record_path('codecraft-capabilities-asr'),lambda record:record['files'].pop('scripts/transcribe.py'))
        rejected(lambda:contracts.load_package(root,'codecraft-capabilities-asr'),'reviewed release')
    with fixture() as root:
        (root/'tools/skill_packages/import.json').unlink()
        rejected(lambda:contracts.load_package(root,'codecraft-capabilities-asr'),'missing reference')


def test_explicit_selection_rejects_unknown_and_duplicate_package_ids():
    choice=cloud_choice();choice['skill']='codecraft-missing'
    rejected(lambda:contracts.selection(ROOT,choice),'missing reference')
    rejected(lambda:contracts.selected_graph(ROOT,[cloud_choice(),cloud_choice()]),'duplicate Skill')
    with fixture() as root:
        write_json(root/'skills/codecraft-unregistered/contract.json',{'id':'codecraft-unregistered'})
        rejected(lambda:contracts.registrations(root),'matching owner')


def test_failed_skill_validation_preserves_application_rules_and_lock():
    with tempfile.TemporaryDirectory() as folder:
        app=Path(folder)/'app'
        generate_project(Catalog(ROOT),'linux/reterminal','buttons_evdev',app,[cloud_choice()])
        rules=(app/'AGENTS.md').read_bytes();lock=(app/'codecraft.lock').read_bytes()
        data=read_json(app/'project.yaml')
        data['brief']['purpose']='Reviewed next application intent'
        data['skills'][0]['environment']['privacy_approved']=False
        write_json(app/'project.yaml',data)
        rejected(lambda:lock_project(app),'unknown')
        assert (app/'AGENTS.md').read_bytes()==rules and (app/'codecraft.lock').read_bytes()==lock


def test_llm_contract_retains_exclusive_input_and_stream_completion_semantics():
    record,contract=contracts.load_package(ROOT,'codecraft-capabilities-llm')
    rejected(lambda:contracts.payload(contract['operations']['complete']['input'],{'prompt_file':'/a','messages_file':'/b'}),'exactly one')
    assert contract['operations']['stream']['output']['type']=='string'
    assert contract['limits']['stream_completion_required'] is True
    choice=cloud_choice();choice['skill']='codecraft-capabilities-llm';choice['configuration']={'max_tokens':0}
    rejected(lambda:contracts.selection(ROOT,choice),'below minimum')


def test_private_environment_files_are_not_locked_or_packaged():
    with tempfile.TemporaryDirectory() as folder:
        output=Path(folder)/'app'
        generate_project(Catalog(ROOT),'linux/reterminal','buttons_evdev',output)
        (output/'.env').write_text('SYNTHETIC_TEST_PRIVATE_VALUE=not-a-credential\n')
        (output/'secrets').mkdir();(output/'secrets/device.json').write_text('{"synthetic":true}')
        lock=lock_project(output)
        assert '.env' not in lock['files'] and 'secrets/device.json' not in lock['files']
        package_project(output,Path(folder)/'package.zip')
        import zipfile
        with zipfile.ZipFile(Path(folder)/'package.zip') as archive:
            assert '.env' not in archive.namelist() and 'secrets/device.json' not in archive.namelist()


def cloud_choice():
    return {'skill':'codecraft-capabilities-asr','configuration':{},
            'environment':{'network':True,'tls':True,'privacy_approved':True,
                           'environment_refs':['CODECRAFT_API_ORIGIN'],'secret_refs':['CODECRAFT_DEVICE_FILE']},'limits':{}}


def test_cloud_package_checks_need_no_hardware_catalog():
    with tempfile.TemporaryDirectory() as folder:
        root=Path(folder)/'cloud-only'
        for relative in contracts.package_graph(ROOT,'codecraft-capabilities-asr').files:
            destination=root/relative;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/relative,destination)
        assert not (root/'devices').exists() and not (root/'platforms').exists()
        run=subprocess.run([sys.executable,'-B',str(ROOT/'codecraft.py'),'--root',str(root),'check-cloud-skills'],
                           cwd=folder,capture_output=True,text=True,timeout=30)
        assert run.returncode==0,run.stdout+run.stderr
        assert json.loads(run.stdout)['ok']
        assert contracts.selection(root,cloud_choice())['status']=='eligible'
    rejected(lambda:Catalog(ROOT).context('linux/nonexistent',selected_skills=[cloud_choice()]),'unknown Target')


def test_malformed_cloud_selections_are_not_silently_dropped():
    c = Catalog(ROOT)
    with tempfile.TemporaryDirectory() as folder:
        output = Path(folder)/'application'
        for invalid in ({}, False, '', [None]):
            rejected(lambda: generate_project(c, 'linux/reterminal', 'buttons_evdev', output, invalid), 'selection')
            assert not output.exists()
        selections = Path(folder)/'null-selection.json'
        write_json(selections, None)
        run = subprocess.run([sys.executable, str(ROOT/'codecraft.py'), 'new',
                              '--target', 'linux/reterminal', '--example', 'buttons_evdev',
                              '--output', str(output), '--skills', str(selections)],
                             capture_output=True, text=True, timeout=30)
        assert run.returncode != 0 and not output.exists()
        generate_project(c, 'linux/reterminal', 'buttons_evdev', output)
        edit(output, 'project.yaml', lambda data: data.update(skills={}))
        rejected(lambda: lock_project(output), 'selections must be a list')
    contract=contracts.load_package(ROOT,'codecraft-capabilities-asr')[1]
    for invalid in ([],False,''):
        rejected(lambda:contracts.prerequisites(contract,invalid),'must be objects')
        rejected(lambda:contracts.prerequisites(contract,limits=invalid),'must be objects')


def test_pinned_skill_binary_assets_survive_context_export_lock_and_package():
    import zipfile
    with fixture() as root, tempfile.TemporaryDirectory() as folder:
        asset = 'skills/codecraft-capabilities-asr/assets/vocabulary.bin'
        path = root/asset
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b'\x00synthetic packaged vocabulary\xff')
        edit(root, contracts.record_path('codecraft-capabilities-asr'),
             lambda record: record['files'].update({'assets/vocabulary.bin': digest(path)}))
        catalog = Catalog(root)
        assert asset in catalog.context('linux/reterminal', selected_skills=[cloud_choice()])['files']
        output = Path(folder)/'application'
        generate_project(catalog, 'linux/reterminal', 'buttons_evdev', output, [cloud_choice()])
        assert (output/asset).read_bytes() == path.read_bytes()
        assert read_json(output/'codecraft.lock')['files'][asset] == digest(path)
        assert verify_project(output)['status'] == 'passed'
        package = Path(folder)/'application.zip'
        package_project(output, package)
        with zipfile.ZipFile(package) as archive:
            assert archive.read(asset) == path.read_bytes()
        (output/asset).write_bytes(b'changed asset')
        assert asset in verify_project(output)['drift']


def test_contract_rejects_ambiguous_or_malformed_cli_mappings():
    record,original=contracts.load_package(ROOT,'codecraft-capabilities-llm')
    for fixed in ('--stream',['--stream','--stream'],[42]):
        contract=copy.deepcopy(original);contract['client']['operations']['stream']['fixed_arguments']=fixed
        rejected(lambda:contracts.validate_contract(contract,record['files']),'CLI' if isinstance(fixed,list) else 'fixed arguments')
    contract=copy.deepcopy(original)
    contract['client']['operations']['complete']['options']['max_tokens']='--prompt-file'
    rejected(lambda:contracts.validate_contract(contract,record['files']),'duplicate CLI flags')
