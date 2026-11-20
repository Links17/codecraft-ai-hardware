"""The original pin/example checks now cover every discovered ESP-IDF Target."""
from pathlib import Path
import re
import sys
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools/codecraft'))
from model import Catalog
from io_utils import read_json


def test_every_native_target_has_a_manifest():
    catalog=Catalog(ROOT)
    actual={p.parent.parent.name for p in ROOT.glob('devices/*/targets/target.json')
            if read_json(p)['platform']=='esp-idf'}
    assert actual=={t['device'] for t in catalog.targets.values() if t['platform']=='esp-idf'}


def test_every_pin_header_preserves_license_and_unique_defines():
    for target in Catalog(ROOT).targets.values():
        if target['platform']!='esp-idf':continue
        text=(ROOT/target['path']/'bsp/include/bsp_pins.h').read_text()
        assert 'SPDX-License-Identifier: Apache-2.0' in text
        definitions=re.findall(r'^#define\s+(BSP_\w+)\b',text,re.M)
        assert len(definitions)==len(set(definitions))


def test_manifest_examples_match_native_projects_and_bsp_bindings():
    for target in Catalog(ROOT).targets.values():
        if target['platform']!='esp-idf':continue
        path=ROOT/target['path']
        actual={p.parent.name for p in path.glob('examples/*/CMakeLists.txt')}
        assert actual==set(target['examples'])
        for binding in target['interfaces']:
            for source in binding['implementation']:
                assert (ROOT/source).is_file()
        for name in target['examples']:
            assert (path/'examples'/name/'sdkconfig.defaults').is_file()
            lock=path/'examples'/name/'dependencies.lock'
            assert lock.is_file()
            assert str(lock.relative_to(ROOT)) in target['example_dependencies'][name]
