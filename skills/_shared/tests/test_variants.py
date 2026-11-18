"""Sourced hardware selections, portable locks and variant-specific evidence."""
from contextlib import contextmanager
import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'skills/_shared'))
sys.path.insert(0,str(ROOT/'platforms/esp-idf'))
from evidence import support,validate_evidence
from io_utils import ContractError,digest,read_json,write_json
from model import Catalog
from project import generate_project,lock_project,verify_project
from runtime import envelope,load_adapter,run_target
import composition
import variants

TID='esp-idf/sensecap-indicator'


def rejected(action,fragment):
    try:action()
    except ContractError as error:assert fragment in str(error),(fragment,str(error))
    else:raise AssertionError('Expected variant rejection')


@contextmanager
def application(variant='dx'):
    with tempfile.TemporaryDirectory(prefix='codecraft-variant-') as folder:
        root=Path(folder)/'app'
        generate_project(Catalog(ROOT),TID,'display_color_bars',root,variant=variant)
        yield root,Catalog(root)


@contextmanager
def all_variants_application():
    with application('gx') as (root,c):
        target=c.target(TID);destination=root/target['path']
        shutil.copy2(ROOT/target['path']/'variants/dx.cmake',destination/'variants/dx.cmake')
        target['variants']=copy.deepcopy(Catalog(ROOT).target(TID)['variants']);target.pop('selected_variant')
        write_json(destination/'target.json',target)
        yield root,Catalog(root)


def test_sourced_variants_project_only_selected_inputs_without_claiming_revision():
    c=Catalog(ROOT)
    for name in ('gx','dx'):
        context=c.context(TID,'display_color_bars',variant=name)
        target=context['target']
        assert target['selected_variant']==name and set(target['variants'])=={name}
        assert target['path']+'/variants/'+name+'.cmake' in context['files']
        other='gx' if name=='dx' else 'dx'
        assert target['path']+'/variants/'+other+'.cmake' not in context['files']
        assert context['device']['revision']=='unknown'
        assert context['device']['variants'][name]['facts']['compatible_revisions']['status']=='unknown'
    assert c.selected_target(TID,'display_color_bars')['selected_variant']=='gx'
    assert set(c.selected_target(TID)['variants'])=={'gx','dx'}
    rejected(lambda:c.selected_target(TID,variant='unknown'),'unknown variant')
    rejected(lambda:c.selected_target('linux/reterminal',variant='gx'),'unknown variant')


def test_variant_export_lock_origin_and_missing_source_fail_closed():
    for name in ('gx','dx'):
        with application(name) as (root,c):
            target=c.target(TID);profile=read_json(root/'project.yaml');lock=read_json(root/'codecraft.lock')
            assert profile['variant']==lock['variant']==lock['origin']['variant']==name
            assert profile['physical_compatibility']=='unknown'
            path=target['variants'][name]['configuration']['profile']
            assert path in lock['files'] and verify_project(root)['status']=='passed'
            original=(root/path).read_text();(root/path).write_text(original+'\n# edited\n')
            assert verify_project(root)['status']=='failed'
            (root/path).write_text(original)
            profile['variant']='gx' if name=='dx' else 'dx';write_json(root/'project.yaml',profile)
            rejected(lambda:verify_project(root),'profile/lock variant mismatch')
            rejected(lambda:lock_project(root),'profile/Target variant mismatch')
            profile['variant']=name;write_json(root/'project.yaml',profile)
            (root/path).unlink()
            rejected(lambda:Catalog(root),'missing')


def test_variant_metadata_and_native_profiles_reject_unowned_or_conflicting_inputs():
    with application() as (root,c):
        for record in (root/'devices/sensecap-indicator/device.json',root/c.target(TID)['path']/'target.json'):
            original_record=read_json(record)
            assert original_record['schema_version']==3
            for version,variant_state,fragment in ((2,'keep','variant'),(3,'absent','requires variants'),(3,'empty','requires variants'),(999,'keep','unsupported')):
                changed=copy.deepcopy(original_record);changed['schema_version']=version
                if variant_state=='absent':changed.pop('variants')
                elif variant_state=='empty':changed['variants']={}
                write_json(record,changed)
                rejected(lambda:Catalog(root),fragment)
            write_json(record,original_record)
        current=Catalog(ROOT)
        assert current.devices['reterminal']['schema_version']==current.target('linux/reterminal')['schema_version']==2
        target=c.target(TID);path=root/target['path']/'target.json'
        for mutation in ('device','default','selection'):
            changed=copy.deepcopy(target)
            if mutation=='device':changed['variants']['dx']['device_variant']='invented'
            elif mutation=='default':changed['default_variant']='gx'
            else:changed['selected_variant']='gx'
            write_json(path,changed)
            rejected(lambda:Catalog(root),'variant')
        write_json(path,target)
        native=root/target['variants']['dx']['configuration']['profile'];original=native.read_text()
        for text in ('set(CODECRAFT_VARIANT_DEFINES "CODECRAFT_DISPLAY_GX=2")',
                     'set(CODECRAFT_VARIANT_DEFINES "CODECRAFT_DISPLAY_GX=0" "CODECRAFT_DISPLAY_GX=1")',
                     original+'\ninclude(other.cmake)\n'):
            native.write_text(text)
            rejected(lambda:variants.validate(root,target),'variant')
        native.write_text(original)
        target['variants']['dx']['inputs']=[]
        rejected(lambda:variants.validate(root,target),'declared variant input')




def test_adapter_protocol_preserves_explicit_variant_and_rejects_wrong_case_coverage():
    c=Catalog(ROOT);target=c.selected_target(TID,variant='dx');adapter=load_adapter(ROOT,c.platforms['esp-idf'])
    expected=adapter.cases(ROOT,target,'display_color_bars')
    assert expected==[TID+'/display_color_bars/dx']
    payload=envelope(TID,'build',c.graph(TID).fingerprint(),[{'name':expected[0],'status':'passed'}])
    with patch('runtime.subprocess.run',return_value=subprocess.CompletedProcess([],0,json.dumps(payload),'')) as run:
        assert run_target(c,TID,'display_color_bars','dx')[0]['status']=='passed'
        assert run.call_args.args[0][-2:]==['--variant','dx']
    payload['results'][0]['name']=TID+'/display_color_bars/gx'
    with patch('runtime.subprocess.run',return_value=subprocess.CompletedProcess([],0,json.dumps(payload),'')):
        assert run_target(c,TID,'display_color_bars','dx')[0]['status']=='failed'


def test_physical_evidence_never_promotes_unknown_revision_or_another_variant():
    # All observations in this temporary fixture are synthetic. No real Device
    # metadata or evidence is written by this regression.
    with all_variants_application() as (root,c):
        log=root/'devices/sensecap-indicator/tests/logs/fixture.txt';log.parent.mkdir(parents=True,exist_ok=True)
        log.write_text('Synthetic offline evidence fixture. No hardware observations occurred.\n')
        cases=read_json(root/'devices/sensecap-indicator/tests/acceptance.json')['cases']
        record={'schema_version':2,'target':TID,'kind':'device','repository_commit':'1'*40,'repository_dirty':True,
                'source_digest':c.graph(TID).fingerprint(),'revision':'fixture-r1','variant':'gx','toolchain':{'fixture':True},
                'command':['offline-fixture'],'environment':{'fixture':True},'result':'passed','limitations':['synthetic fixture'],
                'operator':'offline regression','log':log.relative_to(root).as_posix(),'log_sha256':digest(log),
                'executed_at':datetime.now(timezone.utc).isoformat(),
                'cases':[{'name':case['id'],'status':'passed','observation':'synthetic fixture','procedure':'offline regression'} for case in cases]}
        records=root/'devices/sensecap-indicator/tests/records';records.mkdir(parents=True)
        write_json(records/'gx.json',record)
        assert support(c,TID)['device']=='not_run'
        missing=copy.deepcopy(record);missing.pop('variant')
        rejected(lambda:validate_evidence(c,missing,current=True),'Physical evidence variant mismatch')
        device_path=root/'devices/sensecap-indicator/device.json';device=read_json(device_path)
        fixture='devices/sensecap-indicator/reference/fixture-revisions.md'
        (root/fixture).write_text('Synthetic test data only. Fixture revision: fixture-r1.\n');device['references'].append(fixture)
        for variant in device['variants'].values():
            fact=variant['facts']['compatible_revisions'];fact.update(status='documented',value=['fixture-r1'],source={'path':fixture,'template':'Fixture revision: {value}.'})
        write_json(device_path,device);c=Catalog(root);record['source_digest']=c.graph(TID).fingerprint();write_json(records/'gx.json',record)
        state=support(c,TID);assert state['variants']['gx']['device']=='passed' and state['variants']['dx']['device']=='not_run' and state['device']=='not_run'
        wrong=copy.deepcopy(record);wrong['revision']='fixture-other'
        rejected(lambda:validate_evidence(c,wrong,current=True),'incompatible')
        record['variant']='dx';write_json(records/'dx.json',record)
        assert support(c,TID)['device']=='passed'


def test_build_evidence_requires_clean_exports_for_every_declared_variant():
    with all_variants_application() as (root,c):
        target=c.target(TID);adapter=load_adapter(root,c.platforms['esp-idf'])
        log=root/'devices/sensecap-indicator/tests/logs/build-fixture.txt';log.parent.mkdir(parents=True,exist_ok=True)
        log.write_text('Synthetic contract fixture; no native compilation is claimed.\n')
        log_fields={'log':log.relative_to(root).as_posix(),'log_sha256':digest(log)}
        checksum=c.graph(TID).fingerprint();children={}
        for variant in ('gx','dx'):
            children[variant]={'variant':variant,'status':'passed','provenance':'passed','origin_source_digest':checksum,
                'source_digest':'2'*64,'build_results':[{'name':TID+'/display_color_bars/'+variant,'status':'passed','variant':{'id':variant}}],**log_fields}
        project={'status':'passed','provenance':'passed','origin_source_digest':checksum,'source_digest':'3'*64,
                 'example':'display_color_bars','variant_projects':children,
                 'build_results':[row for child in children.values() for row in child['build_results']],**log_fields}
        record={'schema_version':2,'target':TID,'kind':'build','repository_commit':'1'*40,'repository_dirty':True,
                'source_digest':checksum,'revision':'unknown','toolchain':{'fixture':True},'command':['offline-fixture'],
                'environment':{'fixture':True},'result':'passed','limitations':['synthetic fixture'],'operator':'offline regression',
                'executed_at':datetime.now(timezone.utc).isoformat(),**log_fields,'generated_project':project,
                'cases':[{'name':name,'status':'passed','toolchain':{'fixture':True}} for name in adapter.cases(root,target)]}
        validate_evidence(c,record,current=True)
        broken=copy.deepcopy(record);del broken['generated_project']['variant_projects']['dx']
        rejected(lambda:validate_evidence(c,broken,current=True),'cover every variant')
        broken=copy.deepcopy(record);broken['generated_project']['variant_projects']['dx']['build_results'][0]['variant']['id']='gx'
        rejected(lambda:validate_evidence(c,broken,current=True),'variant build mismatch')


def test_public_cli_exports_selected_variant_and_reports_unknown_selection():
    with tempfile.TemporaryDirectory(prefix='codecraft-variant-cli-') as folder:
        output=Path(folder)/'app'
        result=subprocess.run([sys.executable,str(ROOT/'codecraft.py'),'new','--target',TID,'--example','display_color_bars','--variant','dx','--output',str(output)],capture_output=True,text=True)
        data=json.loads(result.stdout);assert result.returncode==0 and data['ok'] and data['data']['variant']=='dx',result.stdout
        assert read_json(output/'codecraft.lock')['variant']=='dx'
        result=subprocess.run([sys.executable,str(ROOT/'codecraft.py'),'context','--target',TID,'--variant','unknown'],capture_output=True,text=True)
        data=json.loads(result.stdout);assert result.returncode==1 and not data['ok'] and 'unknown variant' in data['error']['message']
