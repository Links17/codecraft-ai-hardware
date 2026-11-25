"""Public firmware commands distinguish unsupported profiles and missing builds."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[3]


def test_firmware_cli_reports_unsupported_platform_and_format_without_writing():
    with tempfile.TemporaryDirectory() as folder:
        output=Path(folder)/'plan.json'
        for target,example,options in [('linux/reterminal','buttons_evdev',[]),
                                       ('arduino/wio-terminal','display_buttons',[]),
                                       ('esp-idf/sensecap-watcher','battery_status',['--format','hex'])]:
            run=subprocess.run([sys.executable,str(ROOT/'tools/codecraft/maintenance.py'),'firmware','plan','--target',target,
                                '--example',example,'--output',str(output),*options],capture_output=True,text=True)
            data=json.loads(run.stdout)
            assert run.returncode==2 and data['data']['status']=='not_supported',data
            assert not output.exists()


def test_firmware_cli_rejects_invalid_plans_with_a_typed_error():
    with tempfile.TemporaryDirectory() as folder:
        path=Path(folder)/'plan.json';path.write_text('{}')
        output=Path(folder)/'release'
        run=subprocess.run([sys.executable,str(ROOT/'tools/codecraft/maintenance.py'),'firmware','merge','--plan',str(path),
                            '--output',str(output)],capture_output=True,text=True)
        assert run.returncode==1 and json.loads(run.stdout)['error']['type']=='contract'
        assert not output.exists()
