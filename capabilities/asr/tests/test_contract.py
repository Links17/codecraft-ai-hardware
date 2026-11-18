"""Cloud Skill contract tests; no network request or credential access."""
import copy
import io
from pathlib import Path
import sys
import wave
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'skills/_shared'))
from model import Catalog
from io_utils import ContractError
sys.path.insert(0, str(ROOT/'capabilities/_tests'))
from skill_harness import local_skill, invoke_contract

CID='asr'
OP='transcribe'
INPUT={'file': '/user/recording.wav'}
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


def test_prepared_transcription_matches_actual_client_contract():
    with local_skill() as (case, cloud):
        output = invoke_contract(case, cloud, CID, OP, {'file': str(case.audio)})
        assert output == {'text': 'hello'}
        assert case.audio.read_bytes() in case.requests[0][2]


def test_prepared_invalid_audio_fails_before_api_execution():
    with local_skill() as (case, cloud):
        case.audio.write_bytes(b'not a WAV file')
        invoke_contract(case, cloud, CID, OP, {'file': str(case.audio)}, succeeds=False)
        assert case.requests == []


def test_provider_audio_boundaries_are_enforced_by_the_isolated_client():
    with local_skill() as (case, cloud):
        limits = cloud.providers[CID+'/codecraft-cloud']['policy']['limits']
        assert (limits['container'], limits['encoding'], limits['channels'], limits['sample_bits']) == ('WAV', 'PCM', 1, 16)

        def recording(rate, seconds, channels=1, bits=16):
            buffer = io.BytesIO()
            with wave.open(buffer, 'wb') as audio:
                audio.setnchannels(channels)
                audio.setsampwidth(bits//8)
                audio.setframerate(rate)
                audio.writeframes(bytes(rate*seconds*channels*(bits//8)))
            return buffer.getvalue()

        rates = limits['sample_rate_hz']
        duration = limits['maximum_duration_seconds']
        for rate in (rates['minimum'], rates['maximum']):
            case.audio.write_bytes(recording(rate, duration))
            assert invoke_contract(case, cloud, CID, OP, {'file': str(case.audio)}) == {'text': 'hello'}
        before = len(case.requests)
        invalid = [recording(rates['minimum'], duration+1),
                   recording(rates['minimum']-1, 1), recording(rates['maximum']+1, 1),
                   recording(rates['minimum'], 1, channels=2), recording(rates['minimum'], 1, bits=8),
                   bytes(limits['maximum_file_bytes']+1)]
        for content in invalid:
            case.audio.write_bytes(content)
            invoke_contract(case, cloud, CID, OP, {'file': str(case.audio)}, succeeds=False)
        assert len(case.requests) == before
