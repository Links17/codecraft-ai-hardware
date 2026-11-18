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

CID='image-generation'
OP='generate'
INPUT={'prompt_file': '/user/prompt.txt', 'output': '/user/image.png'}
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


def test_prepared_local_and_archived_image_match_actual_output_contract():
    with local_skill() as (case, cloud):
        for archive in (False, True):
            destination = case.directory/('archived.png' if archive else 'local.png')
            before = len(case.requests)
            output = invoke_contract(case, cloud, CID, OP,
                                     {'prompt_file': str(case.prompt), 'output': str(destination)},
                                     {'archive': archive})
            assert output['file'] == str(destination.resolve())
            assert destination.read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
            assert len(case.requests) == before+(2 if archive else 1)
            request = json.loads(case.requests[before][2])
            assert (request['n'], request['size'], request['response_format']) == (1, '1024x1024', 'b64_json')
            if archive:
                assert output['authentication'] == 'Device header required'
                assert output['content_url'].startswith(case.origin+'/deviceapi/media-assets/')
            else:
                assert set(output) == {'file'}


def test_prepared_image_rejects_existing_output_before_api_execution():
    with local_skill() as (case, cloud):
        destination = case.directory/'existing.png'
        destination.write_bytes(b'existing user file')
        invoke_contract(case, cloud, CID, OP,
                        {'prompt_file': str(case.prompt), 'output': str(destination)}, succeeds=False)
        assert destination.read_bytes() == b'existing user file' and case.requests == []


def test_provider_prompt_bound_and_request_size_reach_the_isolated_client():
    with local_skill() as (case, cloud):
        limits = cloud.providers[CID+'/codecraft-cloud']['policy']['limits']
        maximum = limits['maximum_prompt_characters']
        case.prompt.write_text('a'*maximum)
        destination = case.directory/'maximum.png'
        invoke_contract(case, cloud, CID, OP, {'prompt_file': str(case.prompt), 'output': str(destination)})
        request = json.loads(case.requests[-1][2])
        assert request['size'] == str(limits['width'])+'x'+str(limits['height'])
        assert request['n'] == cloud.capabilities[CID]['limits']['count']
        case.prompt.write_text('a'*(maximum+1))
        rejected = case.directory/'oversized.png'
        invoke_contract(case, cloud, CID, OP, {'prompt_file': str(case.prompt), 'output': str(rejected)}, succeeds=False)
        assert not rejected.exists() and len(case.requests) == 1
