"""Authored Markdown, single-source facts, citations and portable locked guidance."""
from contextlib import contextmanager
import copy
from pathlib import Path
import shutil
import tempfile

from device_entry import read_entry, read_contract, source_notes, write_contract
from model import Catalog
from project import generate_project, verify_project
from render import generate
from cli import check_documentation
from io_utils import ContractError, digest, source_files

ROOT = Path(__file__).resolve().parents[3]


@contextmanager
def fixture():
    with tempfile.TemporaryDirectory(prefix='codecraft-device-entry-') as folder:
        root = Path(folder)
        for source in source_files(ROOT):
            destination = root/source.relative_to(ROOT)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        yield root


def change(root, relative, update):
    data = read_contract(root/relative)
    update(data)
    write_contract(root/relative, data)


def rejected(operation, message):
    try:
        operation()
    except ContractError as exc:
        assert message in str(exc), str(exc)
    else:
        raise AssertionError('Expected rejection: '+message)


def test_generation_preserves_authored_bytes_and_updates_only_indexes():
    with fixture() as root:
        path=root/'devices/reterminal/AGENTS.md'
        path.write_text(path.read_text()+'\n## Operator notes\n\nKeep this authored appendix.\n')
        before=path.read_bytes()
        catalog=Catalog(root);fingerprint=catalog.graph('linux/reterminal').fingerprint()
        generate(catalog)
        assert path.read_bytes()==before
        assert generate(Catalog(root),check=True)==[]
        assert Catalog(root).graph('linux/reterminal').fingerprint()==fingerprint
        change(root,'devices/reterminal/AGENTS.md',lambda d:d.update(overview='A maintained overview.'))
        drift=generate(Catalog(root),check=True)
        assert 'devices/AGENTS.md' in drift and 'devices/reterminal/AGENTS.md' not in drift
        assert Catalog(root).graph('linux/reterminal').fingerprint()!=fingerprint


def test_specification_cells_cannot_certify_their_own_facts():
    with fixture() as root:
        path=root/'devices/reterminal/AGENTS.md'
        data=read_contract(path)
        data['facts']['mcu']['source']={'path':'devices/reterminal/AGENTS.md','template':'SELF_CERT: {value}'}
        write_contract(path,data)
        rejected(lambda:Catalog(root),'contradicts cited source')
        path.write_text(path.read_text().replace('## Hardware notes','## Hardware notes\n\nSELF_CERT: CM4',1))
        Catalog(root)


def test_generation_preserves_crlf_and_markdown_edits_preserve_source_notes():
    with fixture() as root:
        path=root/'devices/reterminal/AGENTS.md'
        original=path.read_text().replace('\n','\r\n');path.write_bytes(original.encode())
        notes=source_notes(original,str(path))
        generate(Catalog(root));assert path.read_bytes()==original.encode()
        change(root,'devices/reterminal/AGENTS.md',lambda d:d.update(overview='An edited overview.'))
        assert source_notes(read_entry(path),str(path))==notes
        assert read_contract(path)['overview']=='An edited overview.'


def test_markdown_structure_and_citations_fail_without_rewriting_documents():
    with fixture() as root:
        path=root/'devices/reterminal/AGENTS.md';original=read_entry(path)
        malformed=[(original.replace('## Specifications','## Missing'), 'missing Device Markdown'),
                   (original+'\n## Profile\n\nDuplicate\n','duplicate section'),
                   (original.replace('| ID | reterminal |','| ID | reterminal |\n| ID | other |'),'duplicate profile'),
                   (original+'\n[device-notes]: elsewhere.md\n','duplicate reference'),
                   (original.replace('[device-notes][device-notes]','[device-notes][missing]'),'undefined reference')]
        for text,reason in malformed:
            path.write_bytes(text.encode())
            rejected(lambda:read_contract(path),reason)
            assert read_entry(path)==text


def test_acceptance_changes_source_identity_and_has_one_maintained_copy():
    with fixture() as root:
        path=root/'devices/reterminal/AGENTS.md'
        before=Catalog(root).graph('linux/reterminal').fingerprint()
        procedure='Record the independently identified unit and measured revision.'
        change(root,'devices/reterminal/AGENTS.md',lambda d:d['acceptance']['cases'][0].update(procedure=procedure))
        assert read_entry(path).count(procedure)==1
        assert Catalog(root).graph('linux/reterminal').fingerprint()!=before
        original=path.read_bytes();generate(Catalog(root));assert path.read_bytes()==original


def test_absent_assets_need_no_placeholder_and_declared_assets_must_exist():
    with fixture() as root:
        path=root/'devices/reterminal/AGENTS.md'
        assert not (path.parent/'assets').exists() and '## Assets' not in read_entry(path)
        data=read_contract(path);data['assets']=None
        rejected(lambda:write_contract(path,data),'assets must be a list')
        data=read_contract(path);data.update(revision='fixture',assets=[{
            'path':'devices/reterminal/assets/missing.png','source':'synthetic fixture','license':'CC0',
            'sha256':'0'*64,'revision':'fixture','width':1,'height':1,'alpha':False}])
        write_contract(path,data)
        rejected(lambda:Catalog(root),'missing reference')


def test_typed_facts_and_reserved_fields_are_deterministic():
    with fixture() as root:
        path=root/'devices/reterminal-e1001/AGENTS.md';data=read_contract(path)
        write_contract(path,data);assert read_contract(path)==data
        original=read_entry(path)
        bad=original.replace('| integer | 32 |','| integer | thirty-two |',1)
        assert bad!=original
        path.write_text(bad);rejected(lambda:read_contract(path),'invalid integer')
        path.write_text(original)
        data['targets']=['esp-idf/reterminal-e1001']
        rejected(lambda:write_contract(path,data),'unsupported Device fields')


def test_full_device_markdown_is_hashed_without_content_projections():
    catalog=Catalog(ROOT);graph=catalog.graph('linux/reterminal').snapshot()
    relative='devices/reterminal/AGENTS.md'
    assert graph['schema_version']==3 and 'projections' not in graph
    assert graph['files'][relative]==digest(ROOT/relative)


def test_export_keeps_the_complete_authored_document_and_locks_every_byte():
    catalog=Catalog(ROOT)
    with tempfile.TemporaryDirectory() as folder:
        output=Path(folder)/'project'
        generate_project(catalog,'linux/reterminal','buttons_evdev',output)
        path=output/'devices/reterminal/AGENTS.md'
        assert path.read_bytes()==(ROOT/'devices/reterminal/AGENTS.md').read_bytes()
        assert not list((output/'devices').glob('*/device.json'))
        check_documentation(output)
        assert verify_project(output)['status']=='passed'
        path.write_text(path.read_text()+'\nAn unreviewed hardware claim.\n')
        assert verify_project(output)['drift']==['devices/reterminal/AGENTS.md']
