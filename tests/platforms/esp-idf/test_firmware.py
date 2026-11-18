"""Factory image boundaries; synthetic addresses are test data, not board facts."""
import copy
import hashlib
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'skills/_shared'))
sys.path.insert(0, str(ROOT/'platforms/esp-idf'))
from io_utils import ContractError, OperationUnavailable, digest, read_json, write_json
from device_entry import read_contract, write_contract
import esp_firmware as native


def rejected(call, fragment):
    try:
        call()
    except (ContractError, OSError) as exc:
        assert fragment.lower() in str(exc).lower(), str(exc)
    else:
        raise AssertionError('Invalid firmware accepted: '+fragment)


def inputs(root):
    segments = []
    for offset, role in [(0, 'bootloader'), (0x8000, 'partition-table'), (0x10000, 'app'), (0x20000, 'data')]:
        path = root/(role+'.bin')
        path.write_bytes(role.encode().ljust(64, b'\0'))
        segments.append({**native.file_record(root, path), 'offset': offset, 'role': role})
    return {'schema_version': 1, 'chip': 'synthetic', 'address_space': 'flash', 'format': 'bin',
            'purpose': 'factory', 'fill': 255, 'base_address': 0, 'flash_capacity': 0x100000,
            'partition_table_offset': 0x8000, 'flash_settings': {'flash_mode': 'dio', 'flash_freq': '80m', 'flash_size': '1MB'},
            'segments': segments, 'metadata': [], 'tools': {'version': 'synthetic'},
            'write_range': {'start': 0, 'end': 0x20040},
            'partitions': [{'name': 'app', 'type': 0, 'subtype': 0, 'offset': 0x10000, 'size': 0x10000},
                           {'name': 'data', 'type': 1, 'subtype': 2, 'offset': 0x20000, 'size': 0x10000}]}


def tool_fixture(corrupt=None):
    def merge(addr_data, chip, **kwargs):
        assert chip == 'synthetic' and kwargs['flash_size'] == '1MB'
        assert all(isinstance(data, bytes) for _, data in addr_data)
        output = bytearray()
        for address, data in addr_data:
            output.extend(b'\xff'*(address-len(output)))
            output.extend(data)
        if corrupt:
            corrupt(output)
        return bytes(output)
    return SimpleNamespace(cmds=SimpleNamespace(merge_bin=merge),
                           CHIP_DEFS={'synthetic': SimpleNamespace(BOOTLOADER_FLASH_OFFSET=0)})


def test_layout_accepts_extra_data_partitions_and_rejects_conflicts_and_bounds():
    with tempfile.TemporaryDirectory() as folder:
        value = inputs(Path(folder).resolve())
        native.validate_layout(value)
        variants = [
            (lambda d: d['segments'][2].update(offset=0x8000), 'overlapping'),
            (lambda d: d['segments'][0].update(size=0x8001), 'reserved'),
            (lambda d: d['segments'][2].update(size=0x10001), 'outside'),
            (lambda d: d['segments'][3].update(offset=0x20001), 'unaligned'),
            (lambda d: d.update(flash_capacity=0x20000), 'capacity'),
            (lambda d: d.update(base_address=-1), 'base'),
            (lambda d: d['segments'][3].update(role='app'), 'type mismatch'),
            (lambda d: d.update(write_range={'start': 0, 'end': 1}), 'write range'),
        ]
        for change, message in variants:
            broken = copy.deepcopy(value)
            change(broken)
            rejected(lambda: native.validate_layout(broken), message)


def test_inputs_reject_escape_symlink_empty_and_byte_drift():
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder).resolve()
        value = inputs(root)
        first = value['segments'][0]
        (root/first['path']).write_bytes(b'changed')
        rejected(lambda: native.checked_bytes(root, first), 'changed')
        (root/'empty').write_bytes(b'')
        rejected(lambda: native.file_record(root, root/'empty'), 'empty')
        (root/'link').symlink_to(root/'app.bin')
        rejected(lambda: native.file_record(root, root/'link'), 'symlink')
        rejected(lambda: native.file_record(root, root.parent/'outside.bin'), 'escapes')


def test_merge_snapshots_inputs_checks_each_byte_and_preserves_extra_partitions():
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder).resolve()
        value = inputs(root)
        stage = root/'stage'; stage.mkdir()
        tool = tool_fixture()
        with patch.object(native, 'native_tools', return_value=(tool, None, value['tools'])), \
             patch.object(native, 'normalized_bootloader', side_effect=lambda t,c,b,s: b):
            manifest = native.merge(root, value, stage)
        assert len(manifest['regions']) == 4 and manifest['image']['sha256'] == digest(stage/'firmware.bin')
        assert (stage/'firmware.bin').read_bytes()[0x20000:] == (root/'data.bin').read_bytes()
        for offset, message in [(0x10010, 'segment content'), (0x100, 'padding')]:
            tool = tool_fixture(lambda data: data.__setitem__(offset, data[offset] ^ 1))
            with patch.object(native, 'native_tools', return_value=(tool, None, value['tools'])), \
                 patch.object(native, 'normalized_bootloader', side_effect=lambda t,c,b,s: b):
                rejected(lambda: native.merge(root, value, stage), message)


def test_merge_rejects_changed_tools_and_native_failure_without_output():
    with tempfile.TemporaryDirectory() as folder:
        root=Path(folder).resolve(); value=inputs(root); stage=root/'stage'; stage.mkdir()
        with patch.object(native, 'native_tools', return_value=(tool_fixture(), None, {})):
            rejected(lambda: native.merge(root,value,stage), 'tool changed')
        assert not list(stage.iterdir())
        tool=tool_fixture()
        tool.cmds.merge_bin=lambda *a,**k:(_ for _ in ()).throw(RuntimeError('native failure'))
        with patch.object(native, 'native_tools', return_value=(tool,None,value['tools'])):
            rejected(lambda:native.merge(root,value,stage),'native failure')
        assert not list(stage.iterdir())


def test_bootloader_normalization_changes_only_header_and_digest():
    original = bytes(range(64))+b'\0'*32
    chip=SimpleNamespace(parse_flash_size_arg=lambda x: 0x20, parse_flash_freq_arg=lambda x: 0xf)
    tool=SimpleNamespace(CHIP_DEFS={'synthetic':chip}, cmds=SimpleNamespace(FLASH_MODES={'dio':2}))
    with patch.object(native,'image_check',return_value=SimpleNamespace(data_length=64)):
        actual=native.normalized_bootloader(tool,'synthetic',original,{'flash_mode':'dio','flash_freq':'80m','flash_size':'1MB'})
    assert actual[:2]==original[:2] and actual[4:64]==original[4:64]
    assert actual[2:4]==bytes([2,0x2f]) and actual[64:]==hashlib.sha256(actual[:64]).digest()


def test_offline_verification_checks_segments_padding_and_manifest_structure():
    with tempfile.TemporaryDirectory() as folder:
        root=Path(folder).resolve(); value=inputs(root); stage=root/'stage';stage.mkdir(); tool=tool_fixture()
        with patch.object(native,'native_tools',return_value=(tool,None,value['tools'])), \
             patch.object(native,'normalized_bootloader',side_effect=lambda t,c,b,s:b), \
             patch.object(native,'image_check'), \
             patch.object(native,'partition_entries',return_value=value['partitions']):
            manifest=native.merge(root,value,stage);manifest.update(format='bin',purpose='factory')
            write_json(stage/'manifest.json',manifest)
            native.verify(stage,manifest)
            image=stage/'firmware.bin';data=image.read_bytes();image.write_bytes(data[:-1]+b'!')
            rejected(lambda:native.verify(stage,manifest),'SHA-256')
            image.write_bytes(data);manifest['regions'].pop()
            rejected(lambda:native.verify(stage,manifest),'coverage')


def test_security_configuration_is_rejected_before_native_tool_execution():
    with tempfile.TemporaryDirectory() as folder:
        root=Path(folder).resolve();build=root/'.codecraft/builds/fixture/app';build.mkdir(parents=True)
        write_json(build/'flasher_args.json',{'extra_esptool_args':{'chip':'esp32s3'}})
        write_json(build/'config/sdkconfig.json',{'IDF_TARGET':'esp32s3','SECURE_BOOT':True})
        write_json(build/'project_description.json',{'target':'esp32s3'})
        target={'device':'fixture','toolchain':{'target':'esp32s3'}}
        with patch.object(native,'native_tools',side_effect=AssertionError('Unsupported image reached native tool')):
            try:native.layout(root,target,'app')
            except OperationUnavailable as exc:assert exc.status=='not_supported'
            else:raise AssertionError('Signed configuration accepted')


def test_native_partition_verifier_rejects_capacity_and_encrypted_regions():
    item=SimpleNamespace(name='app',type=0,subtype=0,offset=0x10000,size=0x10000,encrypted=False)
    class Table(list):
        def verify(self):pass
    module=SimpleNamespace(PartitionTable=SimpleNamespace(from_binary=lambda data:Table([item])))
    assert native.partition_entries(module,b'synthetic',0x8000,0x20000)[0]['name']=='app'
    rejected(lambda:native.partition_entries(module,b'synthetic',0x8000,0x10000),'capacity')
    item.encrypted=True
    try:native.partition_entries(module,b'synthetic',0x8000,0x20000)
    except OperationUnavailable as exc:assert exc.status=='not_supported'
    else:raise AssertionError('Encrypted partition accepted')


def test_physical_capacity_uses_device_facts_and_preserves_unknowns():
    with tempfile.TemporaryDirectory() as folder:
        root=Path(folder);path=root/'devices/fixture/AGENTS.md';target={'device':'fixture'}
        path.parent.mkdir(parents=True)
        path.write_bytes((ROOT/'devices/reterminal-e1001/AGENTS.md').read_bytes())
        device=read_contract(path);device['id']='fixture'
        device['facts']['flash'].update(value=1)
        write_contract(path,device)
        assert native.physical_capacity(root,target,0x100000)['bytes']==0x100000
        rejected(lambda:native.physical_capacity(root,target,0x200000),'Device limit')
        device['facts']['flash'].update(status='unknown',value=None,reason='Synthetic capacity is unknown.')
        write_contract(path,device)
        assert native.physical_capacity(root,target,0x100000)['status']=='unknown'


def test_native_image_validation_requires_chip_checksum_digest_and_exact_length():
    image=SimpleNamespace(chip_id=9,checksum=7,calculate_checksum=lambda:7,
                          append_digest=True,stored_digest=b'digest',calc_digest=b'digest',data_length=64)
    tool=SimpleNamespace(bin_image=SimpleNamespace(LoadFirmwareImage=lambda c,d:image),
                         CHIP_DEFS={'synthetic':SimpleNamespace(IMAGE_CHIP_ID=9)})
    assert native.image_check(tool,'synthetic',b'\0'*96) is image
    for field,value,message in [('chip_id',1,'chip'),('checksum',0,'checksum'),('stored_digest',b'wrong','SHA-256'),('data_length',32,'trailing')]:
        original=getattr(image,field);setattr(image,field,value)
        rejected(lambda:native.image_check(tool,'synthetic',b'\0'*96),message)
        setattr(image,field,original)
