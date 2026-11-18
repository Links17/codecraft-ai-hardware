"""Provider policy narrows a stable Capability without changing its semantics."""
import copy
from pathlib import Path
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'skills/_shared'))
from io_utils import ContractError, digest, read_json, write_json
from model import Catalog, load_cloud
from project import generate_project, verify_project


def selection(cid, configuration=None):
    return {'capability':cid, 'provider':cid+'/codecraft-cloud',
            'configuration':{} if configuration is None else configuration,
            'environment':{'network':True,'tls':True,'privacy_approved':True,
                           'environment_refs':['CODECRAFT_API_ORIGIN'],
                           'secret_refs':['CODECRAFT_DEVICE_FILE']}, 'limits':{}}


def rejected(fn):
    try:fn()
    except ContractError:return
    raise AssertionError('Invalid Provider policy was accepted')


def test_semantic_contracts_and_service_policy_have_separate_versions():
    cloud=load_cloud(ROOT)
    expected={
        'asr':{'automatic_retry'},
        'llm':{'automatic_retry','roles','text_only','stream_completion_required'},
        'tts':{'automatic_retry'},
        'image-generation':{'automatic_retry','count'},
    }
    for cid,cap in cloud.capabilities.items():
        p=cloud.providers[cid+'/codecraft-cloud']
        assert cap['version']==p['contract_version']=='2.0.0'
        assert set(cap['limits'])==expected[cid] and cap['limits']['automatic_retry'] is False
        assert p['policy']['version']=='1.0.0' and p['skill']['version']=='1.0.2'
        assert set(p['policy']['sources'])<=p['skill']['files'].keys()
        assert not set(p['policy']['limits']) & set(cap['limits'])
        assert p['policy']['billing']['status']=='declared'  # not observed billing


def test_policy_change_updates_cloud_identity_without_changing_capability():
    cloud=load_cloud(ROOT);pid='asr/codecraft-cloud'
    with tempfile.TemporaryDirectory() as folder:
        root=Path(folder)
        for relative in cloud.graph(pid).files:
            out=root/relative;out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/relative,out)
        before=load_cloud(root);fingerprint=before.graph(pid).fingerprint()
        cap_path=root/'capabilities/asr/capability.json';semantic=digest(cap_path)
        path=root/'capabilities/asr/providers/codecraft-cloud/provider.json'
        provider=read_json(path)
        # Synthetic metadata variation, not a second Provider or live price claim.
        provider['policy']['version']='1.0.1'
        provider['policy']['billing']['amount']+=1
        write_json(path,provider)
        after=load_cloud(root)
        assert digest(cap_path)==semantic and after.capabilities['asr']['version']=='2.0.0'
        assert after.graph(pid).fingerprint()!=fingerprint
        item=after.resolve('asr',environment=selection('asr')['environment'])['candidates'][0]
        assert item['provider_policy']['version']=='1.0.1' and item['execution']=='not_run'


def test_defaults_and_configuration_constraints_reach_prepared_arguments():
    cloud=load_cloud(ROOT)
    prepared=cloud.prepare(selection('llm'),None,'complete',{'prompt_file':'/work/input.txt'})
    assert prepared['configuration']=={} and prepared['effective_configuration']=={'max_tokens':256}
    assert prepared['arguments'][-2:]==['--max-tokens','256']
    prepared=cloud.prepare(selection('llm',{'max_tokens':7}),None,'complete',{'prompt_file':'/work/input.txt'})
    assert prepared['arguments'][-2:]==['--max-tokens','7']
    prepared=cloud.prepare(selection('tts'),None,'speak',{'text_file':'/work/input.txt','output':'/work/output.wav'})
    assert prepared['arguments'][-2:]==['--voice','Cherry'] and '--archive' not in prepared['arguments']
    assert prepared['configuration_schema']['properties']['voice']['maxLength']==64
    rejected(lambda:cloud.selection(selection('tts',{'voice':'x'*65})))
    rejected(lambda:cloud.selection(selection('llm',{'max_tokens':False})))
    for cid in ('tts','image-generation'):
        provider=copy.deepcopy(cloud.providers[cid+'/codecraft-cloud'])
        provider['policy']['defaults']['archive']=True
        rejected(lambda:cloud.schema.provider(ROOT,provider,cloud.capabilities[cid]))


def test_missing_malformed_and_incompatible_policy_contracts_fail_closed():
    cloud=load_cloud(ROOT);original=cloud.providers['asr/codecraft-cloud'];cap=cloud.capabilities['asr']
    edits=[lambda p:p.pop('policy'),lambda p:p.update(contract_version='1.0.0'),
           lambda p:p['policy'].update(schema_version=True),lambda p:p['policy'].update(schema_version=99),
           lambda p:p['policy'].update(unrecognized=True),lambda p:p['policy'].update(sources=['not-pinned.md']),
           lambda p:p['policy']['limits'].update(automatic_retry=False),
           lambda p:p['policy']['limits'].update(maximum_file_bytes=-1),
           lambda p:p['policy']['billing'].update(amount=False),
           lambda p:p['policy']['billing'].update(amount=float('nan')),
           lambda p:p['policy']['billing'].update(status='unknown'),
           lambda p:p['policy']['operations'].clear()]
    for edit in edits:
        provider=copy.deepcopy(original);edit(provider)
        rejected(lambda:cloud.schema.provider(ROOT,provider,cap))


def test_schema_constraints_cannot_weaken_or_contradict_the_base():
    cloud=load_cloud(ROOT);schema=cloud.schema
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


def test_provider_output_constraints_preserve_current_archival_contract():
    cloud=load_cloud(ROOT)
    for cid,op in (('tts','speak'),('image-generation','generate')):
        cap=cloud.capabilities[cid];provider=cloud.providers[cid+'/codecraft-cloud']
        base=cap['operations'][op]['output']
        effective=cloud.schema.policy(provider,cap)['operations'][op]['output']
        # The semantic field can describe another authentication scheme; this
        # selected Provider still returns only its pinned client representation.
        output={'file':'/work/result','authentication':'different fixture authentication'}
        cloud.schema.payload(base,output)
        rejected(lambda:cloud.schema.payload(effective,output))
        output['authentication']='Device header required';cloud.schema.payload(effective,output)


def test_selected_policy_is_exported_and_any_drift_invalidates_the_project_lock():
    with tempfile.TemporaryDirectory() as folder:
        output=Path(folder)/'app'
        generate_project(Catalog(ROOT),'linux/reterminal','buttons_evdev',output,[selection('asr')])
        path=output/'capabilities/asr/providers/codecraft-cloud/provider.json'
        assert read_json(path)['policy']==load_cloud(ROOT).providers['asr/codecraft-cloud']['policy']
        assert verify_project(output)['status']=='passed'
        provider=read_json(path);provider['policy']['version']='1.0.1';write_json(path,provider)
        assert verify_project(output)['status']=='failed'
