"""Conservative, reviewed exceptions to native dependency impact.

This is not a Python impact analyser. Only known repository-only CLI branches
and package inventory maintenance are excluded; every other AST change remains
potential native impact. Missing files and executable-mode changes stay visible.
"""
import ast
import copy
from pathlib import Path


HOST_COMMANDS = frozenset({
    'catalog', 'context', 'discover', 'generate', 'test', 'check-cloud-skills',
    'record-evidence', 'skill-release', 'skill-reference', 'ci',
})
HOST_MODULES = frozenset({
    'ci.py', 'ci_policy.py', 'testing.py', 'evidence.py',
    'markdown_docs.py', 'device_entry.py', 'device_validation.py', 'skill_contracts.py',
})


def literal_argument(node):
    if isinstance(node, ast.Constant):
        return True
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return all(literal_argument(value) for value in node.elts)
    if isinstance(node, ast.Name):
        return node.id in {'Path', 'str', 'int', 'float', 'bool'}
    return (isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
            and node.value.id == 'argparse' and node.attr == 'REMAINDER')


def host_guard(node):
    if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.And):
        # Only the first operand can guarantee short-circuiting before native
        # execution sees side effects in the remainder of the condition.
        return host_guard(node.values[0])
    if not (isinstance(node, ast.Compare) and len(node.ops) == 1
            and isinstance(node.left, ast.Attribute) and node.left.attr == 'command'
            and isinstance(node.left.value, ast.Name) and node.left.value.id == 'args'):
        return False
    value = node.comparators[0]
    if isinstance(node.ops[0], ast.Eq) and isinstance(value, ast.Constant):
        return value.value in HOST_COMMANDS
    if isinstance(node.ops[0], ast.In) and isinstance(value, (ast.Set, ast.Tuple, ast.List)):
        return all(isinstance(item, ast.Constant) and item.value in HOST_COMMANDS for item in value.elts)
    return False


def native_cli(body):
    """Keep native dispatch/arguments and every unrecognised statement intact."""
    parsers = set()
    original = copy.deepcopy(body)

    def prune(statements):
        kept = []
        for node in statements:
            call = node.value if isinstance(node, (ast.Assign, ast.Expr)) else None
            if isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute):
                owner = call.func.value
                owner = owner.id if isinstance(owner, ast.Name) else None
                registration = (owner == 'sub' and call.func.attr == 'add_parser' and call.args
                                and isinstance(call.args[0], ast.Constant)
                                and call.args[0].value in HOST_COMMANDS)
                argument = owner in parsers and call.func.attr in {'add_argument', 'add_mutually_exclusive_group'}
                safe_arguments = (all(literal_argument(arg) for arg in call.args)
                                  and all(keyword.arg and literal_argument(keyword.value) for keyword in call.keywords))
                if (registration or argument) and safe_arguments:
                    if isinstance(node, ast.Assign):
                        if not all(isinstance(target, ast.Name) for target in node.targets):
                            kept.append(node)
                            continue
                        parsers.update(target.id for target in node.targets)
                    continue
            if isinstance(node, ast.If):
                if host_guard(node.test):
                    kept.extend(prune(node.orelse))
                    continue
                node.body = prune(node.body)
                node.orelse = prune(node.orelse)
            elif isinstance(node, ast.Try):
                node.body = prune(node.body)
                node.orelse = prune(node.orelse)
                node.finalbody = prune(node.finalbody)
                for handler in node.handlers:
                    handler.body = prune(handler.body)
            kept.append(node)
        return kept

    kept = prune(body)
    nodes = list(ast.walk(ast.Module(body=kept, type_ignores=[])))
    escaped = {node.id for node in nodes if isinstance(node, ast.Name)}
    escaped.update(name for node in nodes if isinstance(node, (ast.Global, ast.Nonlocal)) for name in node.names)
    # A parser binding may shadow a native callable or escape its host-only
    # registration. In that case keep the whole function, conservatively.
    return original if parsers & escaped else kept


def signature(path, content):
    tree = ast.parse(content, filename=path)
    excluded = {'package_inventory'} if path.endswith('/io_utils.py') else {
        'check_documentation', 'static_checks', 'record_evidence',
    }
    tree.body = [node for node in tree.body
                 if not (isinstance(node, ast.FunctionDef) and node.name in excluded
                         and not node.decorator_list and not node.returns
                         and not any(arg.annotation for arg in [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs])
                         and all(literal_argument(arg) for arg in [*node.args.defaults, *filter(None, node.args.kw_defaults)]))]
    if path.endswith('/cli.py'):
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name == 'main':
                node.body = native_cli(node.body)
    return ast.dump(tree, include_attributes=False)


def host_only(path, before, after, *, declared=False):
    """Return an auditable exemption, or None to retain dependency impact."""
    relative = Path(path)
    document = (relative.name in {'README.md', 'README.zh_CN.md', 'README.rst', 'AGENTS.md', 'CLAUDE.md', 'SKILL.md'}
                or path.startswith('docs/'))
    if (relative.suffix.lower() in {'.md', '.rst'} and (document or not declared)
            or relative.name in {'LICENSE', 'NOTICE'}):
        return 'documentation or attribution; static checks remain required'
    if path.startswith('tests/'):
        return 'host tests or retained evidence'
    if path.startswith('tools/codecraft/') and relative.name in HOST_MODULES:
        return 'host validation, metadata or CI maintenance'
    if path in {'tools/codecraft/cli.py', 'tools/codecraft/io_utils.py'}:
        old, new = before / path, after / path
        if old.is_file() and new.is_file() and (old.stat().st_mode & 0o111) == (new.stat().st_mode & 0o111):
            try:
                if signature(path, old.read_text()) == signature(path, new.read_text()):
                    return 'native Python structure unchanged; only reviewed host sections or formatting changed'
            except (SyntaxError, UnicodeError):
                pass  # Static validation will fail; never turn a parse error into a skip.
    return None
