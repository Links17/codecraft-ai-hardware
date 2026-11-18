"""Run standalone clients directly; metadata checks never prepare production calls."""
from contextlib import contextmanager
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'skills/_shared'))
from skill_contracts import load_package, registrations, policy, payload


@contextmanager
def local_skill():
    spec = importlib.util.spec_from_file_location('cloud_protocol_fixture', ROOT/'tests/skills/_cloud/test_protocol.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    case = module.SkillTests()
    case.setUp()
    try:
        yield case, {sid:load_package(ROOT,sid)[1] for sid in registrations(ROOT)}
    finally:
        case.tearDown()


def invoke_contract(case, contracts, name, operation, inputs, configuration=None, succeeds=True):
    sid = 'codecraft-'+name
    contract = contracts[sid]
    mapping = contract['client']['operations'][operation]
    # Supply caller options only: real clients must implement approved defaults.
    args = [*mapping['command'],*mapping['fixed_arguments']]
    for data, flags in ((inputs,mapping['arguments']),(configuration or {},mapping['options'])):
        for key,value in data.items():
            if type(value) is bool:
                if value: args.append(flags[key])
            else:
                args.extend([flags[key],str(value)])
    before = len(case.requests)
    run = case.invoke(sid,Path(mapping['entrypoint']).name,*args)
    if not succeeds:
        assert run.returncode != 0
        return run
    assert run.returncode == 0, run.stderr
    record, _ = load_package(ROOT,sid)
    output_schema = policy(contract,record['files'])['operations'][operation]['output']
    output = run.stdout if output_schema['type']=='string' else json.loads(run.stdout)
    payload(output_schema,output,'actual Skill output')
    assert case.requests[before][0] == contract['api']['operations'][operation]['path']
    assert case.requests[before][1].startswith(contract['api']['authorization']+' ')
    body=case.requests[before][2]
    if body.startswith(b'{'):
        assert not {'model','provider','voice','routing','endpoint'} & json.loads(body).keys()
    else:
        assert b'name="model"' not in body and b'name="provider"' not in body
    return output
