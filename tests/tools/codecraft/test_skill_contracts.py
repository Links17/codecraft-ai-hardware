"""Skill service policy narrows stable semantics without changing them."""
import copy
from pathlib import Path
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'tools/codecraft'))
from io_utils import ContractError, digest, read_json, write_json
from model import Catalog
import skill_contracts as contracts
from project import generate_project, verify_project


def selection(cid, configuration=None):
    return {'skill':'codecraft-capabilities-'+cid,
            'configuration':{} if configuration is None else configuration,
            'environment':{'network':True,'tls':True,'privacy_approved':True,
                           'environment_refs':['CODECRAFT_API_ORIGIN'],
                           'secret_refs':['CODECRAFT_DEVICE_FILE']}, 'limits':{}}


def rejected(fn):
    try:fn()
    except ContractError:return
    raise AssertionError('Invalid Skill service policy was accepted')


def test_semantics_policy_api_and_distribution_versions_remain_independent():
    expected={'asr':{'automatic_retry'},'llm':{'automatic_retry','roles','text_only','stream_completion_required'},
              'tts':{'automatic_retry'},'image-generation':{'automatic_retry','count'}}
    for name, limits in expected.items():
        record, contract=contracts.load_package(ROOT,'codecraft-capabilities-'+name)
        assert contract['schema_version']==2
        assert contract['version']==record['contract_version']=='3.0.0'
        assert contract['policy']['version']==record['policy_version']=='2.0.0'
        assert contract['api']['version']==record['api_version']=='v1'
        assert set(contract['limits'])==limits and contract['limits']['automatic_retry'] is False
        assert set(contract['policy']['sources'])<=record['files'].keys()
        assert not set(contract['policy']['limits']) & limits

        # A documentation release may advance without changing the service contract.
        skill='codecraft-capabilities-'+name
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            for relative in contracts.package_graph(ROOT,skill).files:
                out=root/relative;out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/relative,out)
            major,minor,patch=map(int,record['version'].split('.'))
            next_version=f'{major}.{minor}.{patch+1}'
            entry=root/'skills'/skill/'SKILL.md'
            old_version=f'  version: "{record["version"]}"'
            text=entry.read_text()
            assert text.count(old_version)==1
            entry.write_text(text.replace(old_version,f'  version: "{next_version}"',1))
            updated=copy.deepcopy(record)
            updated['version']=next_version
            updated['files']['SKILL.md']=digest(entry)
            record_path=root/contracts.record_path(skill)
            write_json(record_path,updated)
            loaded,unchanged=contracts.load_package(root,skill)
            assert loaded['version']==next_version and unchanged==contract

            # Independent versions still have to match their owning contract fields.
            for key in ('contract_version','policy_version','api_version'):
                invalid=copy.deepcopy(updated);invalid[key]='99.0.0'
                write_json(record_path,invalid)
                rejected(lambda:contracts.load_package(root,skill))


def test_policy_changes_preserve_semantics_but_require_a_reviewed_package_identity():
    record, original=contracts.load_package(ROOT,'codecraft-capabilities-asr')
    contract=copy.deepcopy(original)
    semantic={k:v for k,v in contract.items() if k!='policy'}
    contract['policy']['version']='2.0.1'
    contract['policy']['billing']['amount']+=1
    contracts.validate_contract(contract,record['files'])
    assert semantic=={k:v for k,v in contract.items() if k!='policy'}
    with tempfile.TemporaryDirectory() as folder:
        root=Path(folder)
        for relative in contracts.package_graph(ROOT,'codecraft-capabilities-asr').files:
            out=root/relative;out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/relative,out)
        before=contracts.package_graph(root,'codecraft-capabilities-asr').fingerprint()
        write_json(root/'skills/codecraft-capabilities-asr/contract.json',contract)
        rejected(lambda:contracts.load_package(root,'codecraft-capabilities-asr'))
        # A synthetic reviewed record, never a live policy or release claim.
        record['files']['contract.json']=digest(root/'skills/codecraft-capabilities-asr/contract.json')
        record['policy_version']='2.0.1';record['version']='2.0.2'
        write_json(root/contracts.record_path('codecraft-capabilities-asr'),record)
        assert contracts.package_graph(root,'codecraft-capabilities-asr').fingerprint()!=before


def test_defaults_require_semantic_permission_and_caller_values_take_precedence():
    assert contracts.selection(ROOT,selection('llm'))['effective_configuration']=={'max_tokens':256}
    assert contracts.selection(ROOT,selection('llm',{'max_tokens':7}))['effective_configuration']=={'max_tokens':7}
    assert contracts.selection(ROOT,selection('tts'))['effective_configuration']=={}
    assert contracts.selection(ROOT,selection('image-generation'))['effective_configuration']=={'size':'1024x1024'}
    rejected(lambda:contracts.selection(ROOT,selection('tts',{'voice':'unsupported'})))
    rejected(lambda:contracts.selection(ROOT,selection('llm',{'max_tokens':2049})))
    rejected(lambda:contracts.selection(ROOT,selection('llm',{'max_tokens':False})))
    for name in ('tts','image-generation'):
        record,contract=contracts.load_package(ROOT,'codecraft-capabilities-'+name)
        contract['policy']['defaults']['archive']=True
        rejected(lambda:contracts.validate_contract(contract,record['files']))


def test_unknown_environment_resources_and_secret_values_fail_selection():
    for sid in contracts.registrations(ROOT):
        record,contract=contracts.load_package(ROOT,sid)
        item=selection(sid.removeprefix('codecraft-capabilities-'))
        assert contracts.prerequisites(contract)['status']=='unknown'
        assert contracts.prerequisites(contract,{'network':False})['status']=='unsupported'
        assert contracts.prerequisites(contract,item['environment'],{'memory_bytes':1024})['status']=='unknown'
        assert contracts.selection(ROOT,item)['device_integration']=='unknown'
        local={**item['environment'],'tls':False,'loopback':True}
        assert contracts.prerequisites(contract,local)['status']=='eligible'
        local['loopback']=False
        assert contracts.prerequisites(contract,local)['status']=='unsupported'
        for key in ('network','tls','privacy_approved','secret_refs','environment_refs'):
            invalid=copy.deepcopy(item);invalid['environment'].pop(key)
            rejected(lambda:contracts.selection(ROOT,invalid))
        for group in ('configuration','environment'):
            invalid=copy.deepcopy(item);invalid[group]['deviceKey']='synthetic-not-a-credential'
            rejected(lambda:contracts.selection(ROOT,invalid))
        for value in (False,[], ''):
            rejected(lambda:contracts.prerequisites(contract,value))
            rejected(lambda:contracts.prerequisites(contract,limits=value))
        for value in (-1,False,'10'):
            rejected(lambda:contracts.prerequisites(contract,limits={'memory_bytes':value}))


def test_malformed_policy_and_versioned_records_are_rejected():
    record,original=contracts.load_package(ROOT,'codecraft-capabilities-asr')
    edits=[lambda c:c.pop('policy'),lambda c:c.update(schema_version=True),
           lambda c:c.update(client=[]),lambda c:c.update(api=[]),lambda c:c.update(prerequisites=[]),
           lambda c:c.update(resources=[]),lambda c:c.update(estimates=[]),lambda c:c.update(limits=[]),
           lambda c:c['client']['operations']['transcribe'].update(arguments=[]),
           lambda c:c['client']['operations']['transcribe'].update(entrypoint='not-pinned.py'),
           lambda c:c['client']['operations']['transcribe'].update(command=['--invalid']),
           lambda c:c['api'].update(model='private-routing'),lambda c:c['api']['operations'].clear(),
           lambda c:c['policy'].update(schema_version=True),lambda c:c['policy'].update(schema_version=99),
           lambda c:c['policy'].update(unrecognized=True),lambda c:c['policy'].update(sources=['not-pinned.md']),
           lambda c:c['policy']['limits'].update(automatic_retry=False),lambda c:c['policy']['limits'].update(bytes=-1),
           lambda c:c['policy']['billing'].update(amount=False),lambda c:c['policy']['billing'].update(amount=float('nan')),
           lambda c:c['policy']['billing'].update(status='unknown'),lambda c:c['policy']['operations'].clear()]
    for edit in edits:
        contract=copy.deepcopy(original);edit(contract)
        rejected(lambda:contracts.validate_contract(contract,record['files']))


def test_output_constraints_preserve_explicit_archival_semantics():
    for name,op in (('tts','speak'),('image-generation','generate')):
        record,contract=contracts.load_package(ROOT,'codecraft-capabilities-'+name)
        output={'file':'/work/result','authentication':'different fixture authentication'}
        contracts.payload(contract['operations'][op]['output'],output)
        effective=contracts.policy(contract,record['files'])['operations'][op]['output']
        rejected(lambda:contracts.payload(effective,output))
        output['authentication']='Device header required';contracts.payload(effective,output)


def test_selected_contract_and_release_drift_invalidate_the_project_lock():
    with tempfile.TemporaryDirectory() as folder:
        output=Path(folder)/'app'
        generate_project(Catalog(ROOT),'linux/reterminal','buttons_evdev',output,[selection('asr')])
        path=output/'skills/codecraft-capabilities-asr/contract.json'
        assert read_json(path)==contracts.load_package(ROOT,'codecraft-capabilities-asr')[1]
        assert verify_project(output)['status']=='passed'
        value=read_json(path);value['policy']['version']='2.0.1';write_json(path,value)
        assert verify_project(output)['status']=='failed'


def test_schema_constraints_cannot_weaken_or_contradict_the_base():
    schema=contracts
    base={'type':'object','description':'Fixture contract','additionalProperties':False,'required':['name'],
          'properties':{'name':{'type':'string','description':'Name','minLength':2,'maxLength':10,'pattern':'[a-z]+'},
                        'count':{'type':'integer','description':'Count','minimum':1,'maximum':10}}}
    overrides=[{'type':'string'},{'properties':{'missing':{}}},{'required':['missing']},
               {'additionalProperties':True},{'properties':{'name':{'minLength':1}}},
               {'properties':{'name':{'maxLength':11}}},{'properties':{'count':{'maximum':11}}},
               {'properties':{'count':{'minimum':False}}},{'properties':{'count':{'minimum':11}}},
               {'properties':{'name':{'maxLength':1}}},{'properties':{'name':{'pattern':'.*'}}},
               {'properties':{'name':{'enum':['invalid-name']}}},{'properties':{'name':{'enum':[]}}}]
    for value in overrides:rejected(lambda:schema.constrained_schema(base,value,'fixture'))
    tightened=schema.constrained_schema(base,{'properties':{'name':{'maxLength':5},'count':{'maximum':3}}},'fixture')
    schema.payload(tightened,{'name':'valid','count':3})
    rejected(lambda:schema.payload(tightened,{'name':'longer','count':3}))
    assert base['properties']['name']['maxLength']==10

