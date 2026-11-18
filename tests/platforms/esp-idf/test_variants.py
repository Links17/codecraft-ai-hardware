"""Actual native compiler metadata must agree with the selected variant profile."""
import copy
from pathlib import Path
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'skills/_shared'))
sys.path.insert(0,str(ROOT/'platforms/esp-idf'))
from io_utils import ContractError,write_json
from model import Catalog
import composition
import variants
TID='esp-idf/sensecap-indicator'


def rejected(action,fragment):
    try:action()
    except ContractError as error:assert fragment in str(error),(fragment,str(error))
    else:raise AssertionError('Expected native variant rejection')


def test_native_variant_evidence_checks_cache_and_every_actual_bsp_compile_definition():
    c=Catalog(ROOT);target=c.target(TID);example='display_color_bars'
    sources=composition.describe(ROOT,target,example)['sources']
    with tempfile.TemporaryDirectory() as folder:
        output=Path(folder)
        cache=output/'CMakeCache.txt';cache.write_text('CODECRAFT_HARDWARE_VARIANT:STRING=dx\n')
        rows=[{'file':str(source),'directory':str(ROOT),'arguments':['cc','-DCODECRAFT_DISPLAY_GX=0','-c',str(source)]} for source in sorted(sources)]
        path=output/'compile_commands.json';write_json(path,rows)
        assert variants.verify_build(ROOT,target,example,'dx',output,sources)['id']=='dx'
        cache.write_text('CODECRAFT_HARDWARE_VARIANT:STRING=gx\n')
        rejected(lambda:variants.verify_build(ROOT,target,example,'dx',output,sources),'actual native variant')
        cache.write_text('CODECRAFT_HARDWARE_VARIANT:STRING=dx\n')
        for flags in ([],['-DCODECRAFT_DISPLAY_GX=1'],['-DCODECRAFT_DISPLAY_GX=0','-DCODECRAFT_DISPLAY_GX=1']):
            changed=copy.deepcopy(rows);changed[0]['arguments']=['cc',*flags,'-c',changed[0]['file']]
            write_json(path,changed)
            rejected(lambda:variants.verify_build(ROOT,target,example,'dx',output,sources),'compiled variant definition')
        write_json(path,rows[:-1])
        rejected(lambda:variants.verify_build(ROOT,target,example,'dx',output,sources),'missing variant compile commands')
