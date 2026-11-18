"""Validate README-only language rules and engineering navigation."""
from pathlib import Path
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'skills/_shared'))
from io_utils import ContractError
from render import paired
from cli import check_documentation


def rejected(fn, contains):
    try:fn()
    except ContractError as exc:assert contains in str(exc),(contains,str(exc))
    else:raise AssertionError('Expected contract rejection')



def test_documentation_policy_requires_readme_pairs_and_rejects_engineering_translations():
    with tempfile.TemporaryDirectory() as folder:
        root=Path(folder)
        for name,text in paired('README.md','# Usage\n','# 使用\n').items():
            (root/name).write_text(text)
        (root/'AGENTS.md').write_text('# Rules\n\nRead [README](README.md).\n')
        check_documentation(root)
        (root/'AGENTS.zh_CN.md').write_text('# Obsolete translation\n')
        rejected(lambda:check_documentation(root),'only README may have a Chinese counterpart')
        (root/'AGENTS.zh_CN.md').unlink()
        (root/'AGENTS.md').write_text('[Obsolete route](AGENTS.zh_CN.md)\n')
        rejected(lambda:check_documentation(root),'broken local link')
        (root/'AGENTS.md').write_text('# Rules\n')
        (root/'README.zh_CN.md').unlink()
        rejected(lambda:check_documentation(root),'missing README Chinese counterpart')
        (root/'README.md').unlink()
        (root/'README.zh_CN.md').write_text('# Orphan\n')
        rejected(lambda:check_documentation(root),'orphan Chinese README')


def test_shared_markdown_references_resolve_once_and_reject_drift():
    with tempfile.TemporaryDirectory() as folder:
        root=Path(folder)
        (root/'guide.md').write_text('# Canonical guide\n')
        entry=root/'AGENTS.md'
        original='# Rules\n\nRead [the guide][shared] and [its requirements][shared].\n\n[shared]: guide.md\n'
        entry.write_text(original);check_documentation(root)
        entry.write_text(original+'\n[Shared]: guide.md\n')
        rejected(lambda:check_documentation(root),'duplicate reference')
        entry.write_text(original.replace('[its requirements][shared]','[requirements][missing]'))
        rejected(lambda:check_documentation(root),'undefined reference')
        entry.write_text(original.replace('guide.md','missing.md'))
        rejected(lambda:check_documentation(root),'broken local link')
        entry.write_text(original+'\n```markdown\n[example][undefined]\n[shared]: example-only.md\n```\n')
        check_documentation(root)
