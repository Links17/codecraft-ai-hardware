"""Firmware receipt freshness, project closure and transactional delivery."""
from contextlib import contextmanager
import copy
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools/codecraft'))
import firmware
from io_utils import ContractError, OperationUnavailable, digest, read_json, write_json
from model import Catalog
from project import generate_project, build_project


def rejected(call, fragment):
    try:call()
    except (ContractError,OSError) as exc:assert fragment.lower() in str(exc).lower(),str(exc)
    else:raise AssertionError('Expected firmware rejection: '+fragment)


@contextmanager
def fixture():
    with tempfile.TemporaryDirectory() as folder:
        root=Path(folder).resolve()
        (root/'source.py').write_text('synthetic source')
        (root/'input.bin').write_bytes(b'synthetic image')
        target={'id':'fixture/board','platform':'fixture','examples':['app'],'firmware':{'formats':['bin']}}
        toolchain={'status':'passed','version':'fixture'}
        adapter=SimpleNamespace(cases=lambda r,t,e=None:['fixture/board/app'],probe=lambda r,t:copy.deepcopy(toolchain),
                                firmware_layout=lambda r,t,example,variant=None:{'input_sha256':digest(root/'input.bin')})
        def selected(tid,example=None,variant=None):
            assert tid==target['id'] and example=='app' and variant is None
            return target
        catalog=SimpleNamespace(root=root,platforms={'fixture':{'operations':{'firmware-'+op:{'supported':True} for op in ('plan','merge','verify')}}},
                                selected_target=selected,graph=lambda tid:SimpleNamespace(fingerprint=lambda:digest(root/'source.py')))
        with patch.object(firmware,'load_adapter',return_value=adapter),patch('model.Catalog',return_value=catalog):
            attempt=firmware.invalidate(catalog,target,'app')
            rows=[{'name':'fixture/board/app','status':'passed','reason':'','firmware_selection':{'example':'app','variant':None}}]
            firmware.finish_build(catalog,target,rows,attempt,firmware.source_identity(catalog,target),copy.deepcopy(toolchain))
            assert rows[0]['status']=='passed',rows
            yield catalog,target,adapter,toolchain


def test_failed_or_pending_build_replaces_previous_successful_receipt():
    with fixture() as (c,t,a,tools):
        firmware.check_receipt(c,t,'app',None,a)
        attempt=firmware.invalidate(c,t,'app')
        try:firmware.check_receipt(c,t,'app',None,a)
        except OperationUnavailable as exc:assert exc.status=='not_run'
        else:raise AssertionError('Pending build reused old image')
        rows=[{'name':'fixture/board/app','status':'failed','reason':'Compiler failed'}]
        firmware.finish_build(c,t,rows,attempt,firmware.source_identity(c,t),tools)
        rejected(lambda:firmware.check_receipt(c,t,'app',None,a),'latest build failed')


def test_source_binary_toolchain_and_selection_drift_block_plans():
    for changed in ('source','binary','toolchain','selection'):
        with fixture() as (c,t,a,tools):
            if changed=='source':(c.root/'source.py').write_text('new source')
            elif changed=='binary':(c.root/'input.bin').write_bytes(b'new image')
            elif changed=='toolchain':tools['version']='changed'
            else:
                p=firmware.receipt_path(c.root,'fixture/board/app');d=read_json(p);d['variant']='other';write_json(p,d)
            rejected(lambda:firmware.plan(c,t['id'],'app'),{'source':'stale','binary':'inputs','toolchain':'toolchain','selection':'selection'}[changed])


def test_plan_digest_and_receipt_identity_are_enforced():
    with fixture() as (c,t,a,tools):
        path=c.root/'plan.json'
        value=firmware.plan(c,t['id'],'app',output=path)['plan']
        rejected(lambda:firmware.plan(c,t['id'],'app',output=path),'exists')
        changed=copy.deepcopy(value);changed['example']='other';write_json(path,changed)
        rejected(lambda:firmware.read_plan(path),'digest')
        write_json(path,value)
        firmware.invalidate(c,t,'app')
        rejected(lambda:firmware.merge(path,c.root/'.codecraft/release'),'new build')
        assert not (c.root/'.codecraft/release').exists()


def test_source_change_during_build_cannot_publish_a_success_receipt():
    with fixture() as (c,t,a,tools):
        attempt=firmware.invalidate(c,t,'app');identity=firmware.source_identity(c,t)
        (c.root/'source.py').write_text('changed while compiling')
        rows=[{'name':'fixture/board/app','status':'passed','reason':'','firmware_selection':{'example':'app','variant':None}}]
        firmware.finish_build(c,t,rows,attempt,identity,tools)
        assert rows[0]['status']=='failed' and 'during build' in rows[0]['reason']
        assert read_json(firmware.receipt_path(c.root,rows[0]['name']))['status']=='not_run'


def test_merge_drift_does_not_publish_or_replace_existing_output():
    with fixture() as (c,t,a,tools):
        plan=c.root/'plan.json';firmware.plan(c,t['id'],'app',output=plan)
        def native_merge(root,layout,stage):
            (stage/'firmware.bin').write_bytes(b'image')
            (root/'source.py').write_text('changed during merge')
            return {'image':{'file':'firmware.bin'}}
        a.firmware_merge=native_merge;a.firmware_verify=lambda b,m:None
        output=c.root/'.codecraft/release'
        rejected(lambda:firmware.merge(plan,output),'stale')
        assert not output.exists()
    with tempfile.TemporaryDirectory() as folder:
        root=Path(folder);stage=root/'stage';stage.mkdir();out=root/'output';out.mkdir()
        (out/'keep').write_text('user file')
        rejected(lambda:firmware.publish(stage,out),'exists')
        assert (out/'keep').read_text()=='user file'


def test_release_path_cannot_enter_versioned_source_through_a_parent_symlink():
    with fixture() as (c,t,a,tools):
        plan=c.root/'plan.json';firmware.plan(c,t['id'],'app',output=plan)
        source=c.root/'source-area';source.mkdir()
        (c.root/'.codecraft/link').symlink_to(source,target_is_directory=True)
        rejected(lambda:firmware.merge(plan,c.root/'.codecraft/link/release'),'under .codecraft')
        assert not list(source.iterdir())


def test_failed_publication_removes_only_its_partial_output():
    with tempfile.TemporaryDirectory() as folder:
        root=Path(folder);stage=root/'stage';stage.mkdir();out=root/'output'
        (stage/'firmware.bin').write_bytes(b'image');(stage/'manifest.json').write_text('{}')
        original=firmware.os.link
        def link(src,dst):
            if Path(dst).name=='manifest.json':raise OSError('synthetic disk failure')
            return original(src,dst)
        with patch.object(firmware.os,'link',side_effect=link):
            rejected(lambda:firmware.publish(stage,out),'disk failure')
        assert not out.exists() and (stage/'firmware.bin').exists()


def test_export_carries_firmware_pipeline_and_failed_preflight_invalidates_receipt():
    with tempfile.TemporaryDirectory() as folder:
        output=Path(folder)/'app'
        generate_project(Catalog(ROOT),'esp-idf/sensecap-watcher','battery_status',output)
        lock=read_json(output/'codecraft.lock')
        for path in ('tools/codecraft/firmware.py','platforms/esp-idf/esp_firmware.py'):
            assert path in lock['files'] and path in lock['dependency_graph']['files']
        case='esp-idf/sensecap-watcher/battery_status'
        p=firmware.receipt_path(output,case);write_json(p,{'status':'passed'})
        (output/'codecraft.py').write_text((output/'codecraft.py').read_text()+'\n# deliberate drift\n')
        rejected(lambda:build_project(output),'Source changed')
        assert read_json(p)['status']=='not_run'


def test_build_and_merge_guards_reject_concurrency_and_release_after_failure():
    with tempfile.TemporaryDirectory() as folder:
        root=Path(folder)
        try:
            with firmware.operation_guard(root,'fixture/one'):
                rejected(lambda:firmware.operation_guard(root,'fixture/one').__enter__(),'Another firmware operation')
                with firmware.operation_guard(root,'fixture/two'):pass
                raise RuntimeError('synthetic interruption')
        except RuntimeError:pass
        with firmware.operation_guard(root,'fixture/one'):pass
