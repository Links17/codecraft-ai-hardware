"""Private project workspaces, brief validation and portable application context."""
from contextlib import contextmanager
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'tools/codecraft'))
from application import destination
from cli import check_documentation
from graph import SourceGraph
from io_utils import ContractError, read_json, source_files, write_json
from model import Catalog
from testing import inventory as test_inventory
from project import generate_project, lock_project, package_project, verify_project


@contextmanager
def reference():
    with tempfile.TemporaryDirectory(prefix='codecraft-projects-test-') as directory:
        root = Path(directory).resolve()/'reference'
        root.mkdir()
        for source in source_files(ROOT, excluded_dirs={'projects'}):
            output = root/source.relative_to(ROOT)
            output.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, output)
        yield root


def rejects(operation, message):
    try:
        operation()
    except ContractError as error:
        assert message.lower() in str(error).lower(), str(error)
    else:
        raise AssertionError('Expected rejection: '+message)


def test_internal_exports_are_portable_on_all_three_platforms():
    with reference() as root:
        catalog = Catalog(root)
        for target in ('esp-idf/reterminal-e1001', 'arduino/grove-beginner-kit', 'linux/reterminal'):
            before = catalog.graph(target).fingerprint()
            output = root/'projects'/target.split('/')[-1]
            generate_project(catalog, target, catalog.target(target)['examples'][0], output)
            assert verify_project(output)['status'] == 'passed'
            lock = read_json(output/'codecraft.lock')
            assert not any(path.startswith('projects/') for path in lock['files'])
            assert 'tools/codecraft/application.py' in lock['files']
            assert catalog.graph(target).fingerprint() == before
            assert 'Purpose: unknown' in (output/'AGENTS.md').read_text()
            assert read_json(output/'project.yaml')['brief']['bom'] == []


def test_project_destinations_protect_reference_sources_and_existing_work():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory).resolve()/'repo'
        root.mkdir()
        for output in (root, root/'projects', root/'platforms/new', root/'devices/new'):
            rejects(lambda: destination(root, output), 'projects/<name>')
        existing = root/'projects/existing'
        existing.mkdir(parents=True)
        (existing/'keep.txt').write_text('preserve')
        rejects(lambda: destination(root, existing), 'new directory')
        assert (existing/'keep.txt').read_text() == 'preserve'
        rejects(lambda: destination(root, root/'projects/../escape'), 'parent traversal')
        external = Path(directory).resolve()/'external-app'
        assert destination(root, external) == external.resolve()


def test_workspace_symlinks_cannot_redirect_generation():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory).resolve()/'repo'
        root.mkdir()
        external = Path(directory).resolve()/'external'
        external.mkdir()
        (root/'projects').symlink_to(external, target_is_directory=True)
        rejects(lambda: destination(root, root/'projects/app'), 'symlink')
        assert not (external/'app').exists()
        alias = Path(directory).resolve()/'alias'
        alias.symlink_to(root, target_is_directory=True)
        rejects(lambda: destination(root, alias/'devices/app'), 'symlink')


def test_brief_relocking_refreshes_agent_context_and_preserves_import_origin():
    with reference() as root:
        output = root/'projects/demo'
        brief = {'name': 'Room display', 'purpose': 'Show local measurements',
                 'target_users': ['Lab staff'], 'scenarios': ['Read the display at a desk'],
                 'bom': [{'item': 'Selected board', 'quantity': 1, 'source': None}]}
        generate_project(Catalog(root), 'linux/reterminal', 'buttons_evdev', output, brief=brief)
        original = read_json(output/'codecraft.lock')['origin']
        context = (output/'AGENTS.md').read_text()
        assert 'Lab staff' in context and 'quantity: 1; source: unknown' in context
        data = read_json(output/'project.yaml')
        data['brief']['purpose'] = 'Report status'
        write_json(output/'project.yaml', data)
        assert verify_project(output)['status'] == 'failed'
        lock_project(output)
        assert 'Purpose: Report status' in (output/'AGENTS.md').read_text()
        assert read_json(output/'codecraft.lock')['origin'] == original
        assert verify_project(output)['status'] == 'passed'
        package_project(output, root.parent/'application.zip')


def test_invalid_briefs_fail_before_creating_output():
    with reference() as root:
        catalog = Catalog(root)
        invalid = [[], {'purpose': ''}, {'target_users': 'everyone'}, {'scenarios': [None]},
                   {'secret': 'synthetic'}, {'bom': [{'item': 'Board', 'quantity': True, 'source': None}]},
                   {'bom': [{'item': 'Board', 'quantity': -1, 'source': None}]}]
        for index, value in enumerate(invalid):
            output = root/'projects'/str(index)
            rejects(lambda: generate_project(catalog, 'linux/reterminal', 'buttons_evdev', output, brief=value), '')
            assert not output.exists()


def test_private_projects_do_not_enter_reference_docs_or_dependency_closure():
    with reference() as root:
        private = root/'projects/private'
        private.mkdir(parents=True)
        (private/'README.md').write_text('[private link](missing.md)')
        (private/'plan.zh_CN.md').write_text('private application notes')
        (private/'test_private.py').write_text('raise AssertionError("must not collect user projects")')
        check_documentation(root)
        assert not any('projects/' in row['name'] for row in test_inventory(root)['tests'])
        rejects(lambda: SourceGraph(root).resolve(['projects/private/README.md']), 'private project')
        assert 'projects/private/README.md' not in Catalog(root).context('linux/reterminal')['files']
        # An explicit application check still validates that application's own docs.
        (private/'project.yaml').write_text('{}')
        rejects(lambda: check_documentation(private), 'counterpart')


def test_public_new_command_accepts_a_brief_and_ideate_context():
    with reference() as root:
        brief = root/'projects/demo.brief.json'
        write_json(brief, {'name': 'CLI demo', 'purpose': 'Exercise a local example'})
        command = [sys.executable, str(root/'codecraft.py'), 'new', '--target', 'linux/reterminal',
                   '--example', 'buttons_evdev', '--output', 'projects/demo', '--brief', str(brief)]
        run = subprocess.run(command, cwd=root, text=True, capture_output=True, timeout=30)
        assert run.returncode == 0, run.stdout+run.stderr
        assert json.loads(run.stdout)['ok'] is True
        assert 'Purpose: Exercise a local example' in (root/'projects/demo/AGENTS.md').read_text()
        context = Catalog(root).context('linux/reterminal', task='ideate')
        assert 'skills/sensecraft-development-ideate/SKILL.md' in context['guidance']
        assert 'skills/sensecraft-development-discover/SKILL.md' in context['guidance']


def test_absent_optional_brief_stays_unknown_when_relocked():
    with reference() as root:
        output = root/'projects/without-brief'
        generate_project(Catalog(root), 'linux/reterminal', 'buttons_evdev', output)
        profile = read_json(output/'project.yaml')
        profile.pop('brief')
        write_json(output/'project.yaml', profile)
        lock_project(output)
        assert verify_project(output)['status'] == 'passed'
        assert '## Bill of materials\n\n- unknown' in (output/'AGENTS.md').read_text()


def test_relocking_preserves_custom_agent_rules():
    with reference() as root:
        output = root/'projects/custom'
        generate_project(Catalog(root), 'linux/reterminal', 'buttons_evdev', output)
        agents = output/'AGENTS.md'
        agents.write_text(agents.read_text() + '\n## Custom rule\n\nKeep the application offline.\n')
        lock_project(output)
        assert 'Keep the application offline.' in agents.read_text()
        # Authored application rules remain intact when adding managed guidance.
        agents.write_text('# Existing application rules\n\nKeep local behavior.\n')
        lock_project(output)
        assert agents.read_text().startswith('# Existing application rules')
        assert 'Keep local behavior.' in agents.read_text()
        assert agents.read_text().count('CODECRAFT_APPLICATION_START') == 1
        assert verify_project(output)['status'] == 'passed'


def test_brief_markup_is_plain_text_not_a_reference_document_link():
    with reference() as root:
        output = root/'projects/prose'
        generate_project(Catalog(root), 'linux/reterminal', 'buttons_evdev', output,
                         brief={'purpose': 'Read [status](not-a-file.md) <offline>\nwith `literal` text'})
        check_documentation(output)
        context = (output/'AGENTS.md').read_text()
        assert '&#91;status&#93;' in context and '&lt;offline&gt;' in context
        assert verify_project(output)['status'] == 'passed'


def test_malformed_generated_markers_do_not_overwrite_custom_rules_or_lock():
    with reference() as root:
        output = root/'projects/markers'
        generate_project(Catalog(root), 'linux/reterminal', 'buttons_evdev', output)
        agents = output/'AGENTS.md'
        agents.write_text(agents.read_text().replace('<!-- CODECRAFT_APPLICATION_END -->', 'Keep this custom text.'))
        before = agents.read_bytes()
        lock = (output/'codecraft.lock').read_bytes()
        rejects(lambda: lock_project(output), 'markers')
        assert agents.read_bytes() == before
        assert (output/'codecraft.lock').read_bytes() == lock


def test_source_aliases_cannot_import_private_projects():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory).resolve()
        private = root/'projects/private'
        private.mkdir(parents=True)
        (private/'source.py').write_text('private = True\n')
        (root/'alias.py').symlink_to(private/'source.py')
        rejects(lambda: SourceGraph(root).resolve(['alias.py']), 'private project')


def test_relocking_does_not_write_through_an_agent_rules_symlink():
    with reference() as root:
        output = root/'projects/linked'
        generate_project(Catalog(root), 'linux/reterminal', 'buttons_evdev', output)
        outside = root.parent/'shared-rules.md'
        outside.write_text('Preserve shared rules.\n')
        agents = output/'AGENTS.md'
        agents.unlink()
        agents.symlink_to(outside)
        lock = (output/'codecraft.lock').read_bytes()
        rejects(lambda: lock_project(output), 'symlink')
        assert outside.read_text() == 'Preserve shared rules.\n'
        assert (output/'codecraft.lock').read_bytes() == lock

def test_local_codegraph_updates_do_not_change_application_source_lock():
    with reference() as root:
        cache = root/'.codegraph'
        cache.mkdir()
        (cache/'index.db').write_bytes(b'reference analysis cache')
        assert not any('.codegraph' in path.parts for path in source_files(root))
        rejects(lambda: SourceGraph(root).resolve(['.codegraph/index.db']), 'generated/cache dependency')
        output = root/'projects/indexed'
        generate_project(Catalog(root), 'linux/reterminal', 'buttons_evdev', output)
        assert not (output/'.codegraph').exists()
        (output/'.codegraph').mkdir()
        index = output/'.codegraph/index.db'
        index.write_bytes(b'application analysis cache')
        assert verify_project(output)['status'] == 'passed'
        index.write_bytes(b'reindexed application cache')
        assert verify_project(output)['status'] == 'passed'
        assert not any(name.startswith('.codegraph/') for name in read_json(output/'codecraft.lock')['files'])
