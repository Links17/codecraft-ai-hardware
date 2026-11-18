"""Validate the actual build inputs and publication of one merged Watcher image."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
from unittest.mock import patch

SCRIPT=Path(__file__).resolve().parents[1]/'tools/merge_image.py'
spec=importlib.util.spec_from_file_location('watcher_merge',SCRIPT)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


def inputs(root):
    data={'extra_esptool_args':{'chip':'esp32s3'},'flash_files':{},
          'flash_settings':{'flash_mode':'dio','flash_freq':'80m','flash_size':'32MB'}}
    for offset in (0,0x8000,0x10000):
        name=f'part-{offset:x}.bin';(root/name).write_bytes(b'\x01'*32);data['flash_files'][hex(offset)]=name
    (root/'flasher_args.json').write_text(json.dumps(data));return data


def rejected(call, fragment):
    try:call()
    except ValueError as error:assert fragment in str(error),str(error)
    else:raise AssertionError('Invalid image layout was accepted')


def test_merge_checks_native_offsets_chip_files_and_overlap():
    with tempfile.TemporaryDirectory() as directory:
        root=Path(directory).resolve();data=inputs(root)
        assert module.merge(root,check_only=True)['status']=='passed'
        assert not (root/module.OUTPUT_NAME).exists()
        data['extra_esptool_args']['chip']='esp32';(root/'flasher_args.json').write_text(json.dumps(data))
        rejected(lambda:module.layout(root),'esp32s3')
        data=inputs(root);data['flash_files']['0x9000']=data['flash_files'].pop('0x8000');(root/'flasher_args.json').write_text(json.dumps(data))
        rejected(lambda:module.layout(root),'0x0, 0x8000, and 0x10000')
        inputs(root);(root/'part-0.bin').write_bytes(b'\0'*0x8001)
        rejected(lambda:module.layout(root),'Overlapping')
        inputs(root);(root/'part-8000.bin').unlink()
        rejected(lambda:module.layout(root),'Missing, empty or escaping')
        data=inputs(root);data['flash_files']['0x0']='../outside.bin';(root/'flasher_args.json').write_text(json.dumps(data))
        rejected(lambda:module.layout(root),'escaping')


def test_merge_uses_checked_inputs_and_never_exposes_a_failed_image():
    with tempfile.TemporaryDirectory() as directory:
        root=Path(directory).resolve();inputs(root);output=root/module.OUTPUT_NAME
        def run(argv,**kwargs):
            assert '@flash_args' not in argv and '--flash-size' in argv
            assert argv[-6:]==['0x0',str(root/'part-0.bin'),'0x8000',str(root/'part-8000.bin'),'0x10000',str(root/'part-10000.bin')]
            Path(argv[argv.index('-o')+1]).write_bytes(b'\0'*(0x10000+32))
        with patch.object(module.subprocess,'run',side_effect=run):
            result=module.merge(root);assert result['bytes']==0x10020 and not result['flashed']
            rejected(lambda:module.merge(root),'already exists')
        output.unlink()
        with patch.object(module.subprocess,'run',side_effect=subprocess.CalledProcessError(1,['esptool'])):
            try:module.merge(root)
            except subprocess.CalledProcessError:pass
            else:raise AssertionError('esptool failure swallowed')
        assert not output.exists()
        with patch.object(module.subprocess,'run',return_value=None):
            rejected(lambda:module.merge(root),'size')
        assert not output.exists()
