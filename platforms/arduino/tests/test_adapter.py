"""Exercise the Arduino CLI boundary without inventing a supported board."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'skills/_shared'))
from runtime import load_adapter
adapter=load_adapter(ROOT,{'id':'arduino','adapter':'platforms/arduino/adapter.py'})
build=adapter.build


def exercise(core_version='1.0.0'):
    with tempfile.TemporaryDirectory() as folder:
        root=Path(folder)
        (root/'native/examples/blink').mkdir(parents=True)
        target={'id':'arduino/test-fixture','device':'test-fixture','platform':'arduino',
                'path':'native','examples':['blink'],
                'toolchain':{'version':'1.5.0','fqbn':'fixture:arch:board','core_version':'1.0.0','libraries':{}}}
        def run(argv,**kwargs):
            if argv[1]=='version':data={'VersionString':'1.5.0'}
            else:data={'platforms':[{'id':'fixture:arch','installed_version':core_version}]}
            return subprocess.CompletedProcess(argv,0,json.dumps(data),'')
        with patch.object(adapter.shutil,'which',return_value='/fixture/arduino-cli'),patch.object(adapter.subprocess,'run',side_effect=run),patch.object(adapter,'command',return_value={'status':'passed'}) as compile_command:
            result=build(root,target)
            return result,compile_command.call_args


def test_installed_core_version_uses_cli_schema_and_native_compile():
    result,call=exercise()
    assert result==[{'status':'passed'}]
    argv=call.args[2]
    assert argv[:4]==['arduino-cli','compile','--fqbn','fixture:arch:board']
    assert argv[-1].endswith('/native/examples/blink')


def test_wrong_core_does_not_compile_or_claim_unsupported_hardware():
    result,call=exercise('2.0.0')
    assert result[0]['status']=='not_run'
    assert call is None
