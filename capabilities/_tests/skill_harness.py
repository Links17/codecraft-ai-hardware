"""Exercise a Capability handoff through an isolated Skill and a loopback API."""
from contextlib import contextmanager
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'skills/_shared'))
from model import load_cloud


@contextmanager
def local_skill():
    spec = importlib.util.spec_from_file_location('cloud_protocol_fixture', ROOT/'skills/_cloud/tests/test_protocol.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    case = module.SkillTests()
    case.setUp()
    try:
        yield case, load_cloud(ROOT)
    finally:
        case.tearDown()


def invoke_contract(case, cloud, capability, operation, inputs, configuration=None, succeeds=True):
    selection = {
        'capability': capability, 'provider': capability+'/codecraft-cloud',
        'configuration': {} if configuration is None else configuration,
        'environment': {'network': True, 'tls': False, 'loopback': True,
                        'privacy_approved': True, 'environment_refs': ['CODECRAFT_API_ORIGIN'],
                        'secret_refs': ['CODECRAFT_DEVICE_FILE']},
        'limits': {},
    }
    before = len(case.requests)
    prepared = cloud.prepare(selection, None, operation, inputs)
    assert prepared['target'] is None and prepared['execution'] == 'not_run'
    assert len(case.requests) == before  # Preparing never invokes the client.
    entry = prepared['entrypoint']
    run = case.invoke(entry['skill'], Path(entry['path']).name, *prepared['arguments'])
    if not succeeds:
        assert run.returncode != 0
        return run
    assert run.returncode == 0, run.stderr
    output = run.stdout if prepared['output_schema']['type'] == 'string' else json.loads(run.stdout)
    cloud.schema.payload(prepared['output_schema'], output, 'actual Skill output')
    provider = cloud.providers[selection['provider']]
    assert case.requests[before][0] == provider['api']['path']
    assert case.requests[before][1].startswith(provider['api']['authorization']+' ')
    assert provider['api']['model'].encode() in case.requests[before][2]
    return output
