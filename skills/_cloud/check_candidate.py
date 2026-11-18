"""Run package and prepared-client checks only against isolated loopback fixtures."""
import importlib.util
import io
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'skills/_shared'))
sys.path.insert(0,str(ROOT/'capabilities/_tests'))
from io_utils import read_json, require, safe_path
from model import load_cloud


def module(name, path):
    spec=importlib.util.spec_from_file_location(name,path)
    loaded=importlib.util.module_from_spec(spec);spec.loader.exec_module(loaded)
    return loaded


def main():
    cloud=load_cloud(ROOT);checks=cloud.check_skills()
    require(all(x['status']=='passed' for x in checks),'Pinned package/CLI check failed')
    source=(ROOT/'skills/_cloud/device_api.py').read_bytes()
    for p in cloud.providers.values():
        if p['kind']=='repository-skill':
            require((ROOT/p['skill']['path']/'scripts/device_api.py').read_bytes()==source,'Candidate helper differs from maintenance source')
    fixture=module('protocol_fixture',ROOT/'skills/_cloud/tests/test_protocol.py')
    suite=unittest.defaultTestLoader.loadTestsFromModule(fixture)
    transcript=io.StringIO();result=unittest.TextTestRunner(stream=transcript).run(suite)
    require(result.testsRun>0 and result.wasSuccessful() and not result.skipped,transcript.getvalue())
    checks.append({'name':'standalone-protocol-suite','status':'passed','cases':result.testsRun})
    coverage=read_json(ROOT/'skills/_cloud/release-checks.json')
    require(set(coverage)==set(cloud.providers),'Release conformance registration must cover every Provider')
    for index,(pid,entry) in enumerate(sorted(coverage.items())):
        require(set(entry['operations'])==set(cloud.providers[pid]['operations']),'Missing operation coverage')
        tests=module('candidate_contract_'+str(index),safe_path(ROOT,entry['path']))
        require(entry['tests'] and len(set(entry['tests']))==len(entry['tests']),'Missing or duplicate conformance test')
        for name in entry['tests']:
            fn=getattr(tests,name);require(callable(fn),'Invalid conformance test')
            fn();checks.append({'name':pid+'::'+name,'status':'passed'})
    print(json.dumps({'status':'passed','checks':checks}))


if __name__=='__main__':
    main()
