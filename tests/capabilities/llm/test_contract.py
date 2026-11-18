"""Cloud Skill contract tests; no network request or credential access."""
import copy
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'skills/_shared'))
from model import Catalog
from io_utils import ContractError
sys.path.insert(0, str(ROOT/'tests/capabilities'))
from skill_harness import local_skill, invoke_contract

CID='llm'
OP='complete'
INPUT={'prompt_file': '/user/prompt.txt'}
CONFIG={'max_tokens': 256}


def selection():
    return {'capability':CID,'provider':CID+'/codecraft-cloud','configuration':copy.deepcopy(CONFIG),
            'environment':{'network':True,'tls':True,'privacy_approved':True,'environment_refs':['CODECRAFT_API_ORIGIN'],'secret_refs':['CODECRAFT_DEVICE_FILE']},'limits':{}}


def reject(fn):
    try:fn()
    except ContractError:return
    raise AssertionError('Invalid cloud Skill contract was accepted')


def test_handoff_uses_pinned_repository_skill_and_never_runs_it():
    c=Catalog(ROOT).cloud()
    prepared=c.prepare(selection(),'linux/reterminal',OP,INPUT)
    assert prepared['execution']=='not_run' and prepared['entrypoint']['skill'].startswith('codecraft-')
    assert prepared['skill']['files']==c.providers[CID+'/codecraft-cloud']['skill']['files']
    assert prepared['skill']['version']==c.providers[CID+'/codecraft-cloud']['skill']['version']
    assert 'CODECRAFT_DEVICE_FILE' in prepared['required_environment']
    assert '--archive' not in prepared['arguments']
    assert 'Authorization' not in prepared and 'deviceKey' not in prepared


def test_unknown_environment_resources_and_negative_network_constraints():
    c=Catalog(ROOT).cloud()
    assert c.resolve(CID,'linux/reterminal')['candidates'][0]['status']=='unknown'
    assert c.resolve(CID,'linux/reterminal',{'network':False})['status']=='unsupported'
    assert c.resolve(CID,'linux/reterminal',selection()['environment'],{'memory_bytes':1024})['candidates'][0]['status']=='unknown'
    assert c.resolve(CID,'linux/reterminal',selection()['environment'])['candidates'][0]['device_integration']=='unknown'
    local=selection()['environment'];local.update(tls=False,loopback=True)
    assert c.resolve(CID,'linux/reterminal',local)['candidates'][0]['status']=='eligible'
    local['loopback']=False
    assert c.resolve(CID,'linux/reterminal',local)['status']=='unsupported'


def test_input_configuration_version_and_secret_values_are_rejected():
    c=Catalog(ROOT).cloud()
    reject(lambda:c.prepare(selection(),'linux/reterminal',OP,{}))
    invalid=selection();invalid['configuration']['api_key']='synthetic-not-a-credential'
    reject(lambda:c.prepare(invalid,'linux/reterminal',OP,INPUT))
    invalid=selection();invalid['environment']['deviceKey']='synthetic-not-a-credential'
    reject(lambda:c.selection(invalid,'linux/reterminal'))
    provider=copy.deepcopy(c.providers[CID+'/codecraft-cloud']);provider['contract_version']='99.0.0'
    reject(lambda:c.schema.provider(ROOT,provider,c.capabilities[CID]))


def test_prepared_prompt_and_messages_match_actual_client_contract():
    with local_skill() as (case, cloud):
        for key, content in [('prompt_file', 'Hello device cloud.'),
                             ('messages_file', [{'role': 'user', 'content': 'Hello device cloud.'}])]:
            source = case.directory/key
            source.write_text(json.dumps(content) if isinstance(content, list) else content)
            output = invoke_contract(case, cloud, CID, 'complete', {key: str(source)}, {'max_tokens': 73})
            assert output == {'text': 'hello', 'usage': {'total_tokens': 2}}
            request = json.loads(case.requests[-1][2])
            assert request['max_tokens'] == 73 and request['stream'] is False
            assert request['messages'] == [{'role': 'user', 'content': 'Hello device cloud.'}]


def test_prepared_stream_requires_done_and_preserves_failure_status():
    with local_skill() as (case, cloud):
        inputs = {'prompt_file': str(case.prompt)}
        assert invoke_contract(case, cloud, CID, 'stream', inputs).strip() == 'hello'
        assert json.loads(case.requests[-1][2])['stream'] is True
        case.mode = 'incomplete'
        before = len(case.requests)
        run = invoke_contract(case, cloud, CID, 'stream', inputs, succeeds=False)
        assert run.stdout == 'hello' and len(case.requests) == before+1


def test_provider_token_default_and_caller_override_reach_the_isolated_client():
    with local_skill() as (case, cloud):
        default = cloud.providers[CID+'/codecraft-cloud']['policy']['defaults']['max_tokens']
        inputs = {'prompt_file': str(case.prompt)}
        for configuration, expected in (({}, default), ({'max_tokens': 7}, 7)):
            invoke_contract(case, cloud, CID, OP, inputs, configuration)
            assert json.loads(case.requests[-1][2])['max_tokens'] == expected
        before = len(case.requests)
        for value in (0, True):
            invalid = selection()
            invalid['configuration'] = {'max_tokens': value}
            reject(lambda: cloud.prepare(invalid, None, OP, inputs))
        assert len(case.requests) == before
