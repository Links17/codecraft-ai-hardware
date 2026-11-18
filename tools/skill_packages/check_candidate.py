"""Run package and standalone-client checks only against isolated loopback fixtures."""
import importlib.util
import io
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/codecraft'))
sys.path.insert(0,str(ROOT/'tests/tools/skill_packages'))
from io_utils import read_json, require, safe_path
from skill_contracts import check_packages, registrations, load_package


def module(name, path):
    spec=importlib.util.spec_from_file_location(name,path)
    loaded=importlib.util.module_from_spec(spec);spec.loader.exec_module(loaded)
    return loaded


def check_suite(name, path):
    fixture=module(name,path)
    suite=unittest.defaultTestLoader.loadTestsFromModule(fixture)
    transcript=io.StringIO();result=unittest.TextTestRunner(stream=transcript).run(suite)
    require(result.testsRun>0 and result.wasSuccessful() and not result.skipped,transcript.getvalue())
    return {'name':name,'status':'passed','cases':result.testsRun}


def main():
    records=registrations(ROOT);checks=check_packages(ROOT)
    require(all(x['status']=='passed' for x in checks),'Pinned package/CLI check failed')
    source=(ROOT/'tools/skill_packages/device_api.py').read_bytes()
    for sid in records:
        require((ROOT/'skills'/sid/'scripts/device_api.py').read_bytes()==source,'Candidate helper differs from maintenance source')
    checks.append(check_suite('standalone-protocol-suite',ROOT/'tests/tools/skill_packages/test_protocol.py'))
    checks.append(check_suite('standalone-onboarding-suite',ROOT/'tests/tools/skill_packages/test_onboarding.py'))
    coverage=read_json(ROOT/'tools/skill_packages/release-checks.json')
    require(set(coverage)==set(records),'Release conformance registration must cover every Skill')
    for index,(pid,entry) in enumerate(sorted(coverage.items())):
        require(set(entry['operations'])==set(load_package(ROOT,pid)[1]['operations']),'Missing operation coverage')
        tests=module('candidate_contract_'+str(index),safe_path(ROOT,entry['path']))
        require(entry['tests'] and len(set(entry['tests']))==len(entry['tests']),'Missing or duplicate conformance test')
        for name in entry['tests']:
            fn=getattr(tests,name);require(callable(fn),'Invalid conformance test')
            fn();checks.append({'name':pid+'::'+name,'status':'passed'})
        for path in entry.get('suites',[]):
            require(path.startswith('tests/skills/'+pid+'/'), 'Skill suite must have its owning path')
            checks.append(check_suite(pid+'::'+Path(path).stem,safe_path(ROOT,path)))
    print(json.dumps({'status':'passed','checks':checks}))


if __name__=='__main__':
    main()
