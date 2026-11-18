"""Cloud Skill contract tests; no network request or credential access."""
import copy
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'skills/_shared'))
from model import Catalog
from io_utils import ContractError
sys.path.insert(0, str(ROOT/'capabilities/_tests'))
from skill_harness import local_skill, invoke_contract

CID='tts'
OP='speak'
INPUT={'text_file': '/user/text.txt', 'output': '/user/speech.wav'}
CONFIG={}


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
    assert prepared['skill']['files'] and prepared['skill']['version']=='1.0.1'
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


def test_prepared_local_and_archived_speech_match_actual_output_contract():
    with local_skill() as (case, cloud):
        for archive in (False, True):
            destination = case.directory/('archived.wav' if archive else 'local.wav')
            before = len(case.requests)
            output = invoke_contract(case, cloud, CID, OP,
                                     {'text_file': str(case.prompt), 'output': str(destination)},
                                     {'archive': archive, 'voice': 'Cherry'})
            assert output['file'] == str(destination.resolve()) and destination.is_file()
            assert json.loads(case.requests[before][2])['voice'] == 'Cherry'
            assert len(case.requests) == before+(2 if archive else 1)
            if archive:
                assert output['authentication'] == 'Device header required'
                assert output['content_url'].startswith(case.origin+'/deviceapi/media-assets/')
            else:
                assert set(output) == {'file'}


def test_prepared_archive_failure_keeps_file_and_nonzero_exit():
    with local_skill() as (case, cloud):
        case.mode = 'archive-fail'
        destination = case.directory/'speech.wav'
        run = invoke_contract(case, cloud, CID, OP,
                              {'text_file': str(case.prompt), 'output': str(destination)},
                              {'archive': True}, succeeds=False)
        assert destination.is_file() and json.loads(run.stdout)['file'] == str(destination.resolve())
        assert len(case.requests) == 2


def test_provider_text_bound_and_default_voice_reach_the_isolated_client():
    with local_skill() as (case, cloud):
        policy = cloud.providers[CID+'/codecraft-cloud']['policy']
        maximum = policy['limits']['maximum_text_characters']
        case.prompt.write_text('a'*maximum)
        destination = case.directory/'maximum.wav'
        invoke_contract(case, cloud, CID, OP, {'text_file': str(case.prompt), 'output': str(destination)})
        request = json.loads(case.requests[-1][2])
        assert request['voice'] == policy['defaults']['voice']
        assert request['response_format'] == policy['limits']['format'].lower()
        assert len(case.requests) == 1
        case.prompt.write_text('a'*(maximum+1))
        rejected = case.directory/'oversized.wav'
        invoke_contract(case, cloud, CID, OP, {'text_file': str(case.prompt), 'output': str(rejected)}, succeeds=False)
        assert not rejected.exists() and len(case.requests) == 1
