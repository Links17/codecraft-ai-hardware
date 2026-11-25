"""Build/check the bundled API reference from source without importing the SDK.

The inventory is deliberately wider than the recommended application API:
compatibility adapters and platform-only entry points remain visible, with
their caller restrictions in api/features.md. Never execute native imports.
"""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess

from io_utils import read_json, require, safe_path

SKILL_ID = "codecraft-development-recamera-pysdk"
REPOSITORY = "https://github.com/Seeed-Studio/recamera-pro-ext-api"
EXCLUDED = {"setup.py", "demo_detect.py", "demo_live.py", "ws_probe.py"}
SPECIAL = {"__init__", "__enter__", "__exit__", "__iter__", "__next__", "__call__", "__or__",
           "__len__", "__getitem__"}
EXTRA_SOURCES = (
    "sdk/include/recamera_ext.h", "market/appmgr/server.py",
    "market/appmgr/workflow_ui.py", "market/appmgr/workflow_models.py",
    "market/appmgr/store_tasks.py", "market/appmgr/result_hub.py",
    "market/appmgr/output_tools.py", "market/appmgr/visualization.py",
    "market/appmgr/workflow_model_contract.py", "market/appmgr/operations.py",
    "sdk/LICENSE", "sdk/NOTICE",
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def documentation(value: str) -> str:
    """Keep reusable contracts, omit upstream test-device account/address."""
    return re.sub(
        r"\b(?:[A-Za-z][\w.-]*@)?(?:192\.168|10\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01]))"
        r"\.\d{1,3}\.\d{1,3}\b", "<device-host>", value)


def discover(root: Path) -> list[Path]:
    """Include new source modules, exclude generated wheels/builds and tests."""
    found = []
    for directory in (root / "kit", root / "sdk/python/recamera_ext"):
        for path in directory.rglob("*.py"):
            relative = path.relative_to(directory)
            if any(p in {"tests", "build", "dist", "__pycache__"} or p.startswith(".")
                   for p in relative.parts[:-1]):
                continue
            if path.name in EXCLUDED or path.name.startswith("test_"):
                continue
            if path.name.startswith("_") and path.name != "__init__.py":
                continue
            found.append(path)
    return sorted(found)


def module_name(path: Path, root: Path) -> str:
    relative = path.relative_to(root).as_posix().removeprefix("sdk/python/")
    return relative.removesuffix(".py").replace("/", ".").removesuffix(".__init__")


def page_name(module: str) -> str:
    return module.replace(".", "-") + ".md"


def public(name: str) -> bool:
    return not name.startswith("_") or name in SPECIAL


def declaration(node: ast.AST) -> str:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        prefix = "async " if isinstance(node, ast.AsyncFunctionDef) else ""
        returns = " -> " + ast.unparse(node.returns) if node.returns else ""
        decorators = "".join("@" + ast.unparse(d) + "\n" for d in node.decorator_list)
        return f"{decorators}{prefix}def {node.name}({ast.unparse(node.args)}){returns}"
    if isinstance(node, ast.ClassDef):
        bases = ", ".join(ast.unparse(b) for b in node.bases)
        decorators = "".join("@" + ast.unparse(d) + "\n" for d in node.decorator_list)
        return decorators + f"class {node.name}" + (f"({bases})" if bases else "")
    return ast.unparse(node)


def assignments(body):
    for i, node in enumerate(body):
        names = []
        if isinstance(node, ast.Assign):
            names = [t.id for t in node.targets if isinstance(t, ast.Name)]
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names = [node.target.id]
        for name in names:
            if not public(name):
                continue
            following = body[i + 1] if i + 1 < len(body) else None
            doc = (following.value.value if isinstance(following, ast.Expr)
                   and isinstance(following.value, ast.Constant)
                   and isinstance(following.value.value, str) else "")
            yield name, node, doc


def module_statements(node):
    """Descend through import guards, never into a class/function scope."""
    for child in ast.iter_child_nodes(node):
        yield child
        if not isinstance(child, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            yield from module_statements(child)


def imports(tree, module, is_package):
    result = {}
    for node in module_statements(tree):
        if isinstance(node, ast.ImportFrom):
            if node.level:
                base = module.split(".") if is_package else module.split(".")[:-1]
                base = base[:len(base) - node.level + 1]
                source = ".".join(base + ([node.module] if node.module else []))
            else:
                source = node.module or ""
            for entry in node.names:
                if (source in {"kit", "recamera_ext"} or source.startswith(("kit.", "recamera_ext."))) and entry.name != "*":
                    result[entry.asname or entry.name] = source + "." + entry.name
        elif isinstance(node, ast.Assign):
            if any(isinstance(t, ast.Name) and t.id == "_EXPORTS" for t in node.targets):
                for name, source in ast.literal_eval(node.value).items():
                    result[name] = module + "." + source + "." + name
    return result


def exported(tree):
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets):
            if isinstance(node.value, (ast.List, ast.Tuple)):
                return set(ast.literal_eval(node.value))
    return None


def http_routes(source: str) -> set[str]:
    """Read literal and regex routes from BaseHTTPRequestHandler methods."""
    tree = ast.parse(source)
    constants = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
            for name in node.targets:
                if isinstance(name, ast.Name):
                    constants[name.id] = node.value.value
    routes = set()
    for method in ast.walk(tree):
        if not isinstance(method, ast.FunctionDef) or method.name not in {
                "do_GET", "do_POST", "do_PUT", "do_DELETE", "do_PATCH", "do_HEAD"}:
            continue
        for node in ast.walk(method):
            values = []
            if isinstance(node, ast.Compare) and isinstance(node.left, ast.Name) and node.left.id == "path":
                for value in node.comparators:
                    if isinstance(value, ast.Constant):
                        values.append(value.value)
                    elif isinstance(value, ast.Name) and value.id in constants:
                        values.append(constants[value.id])
                    else:
                        raise ValueError("Review dynamic HTTP route: " + ast.unparse(node))
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if (isinstance(node.func.value, ast.Name) and node.func.value.id == "re"
                        and node.func.attr in {"fullmatch", "match"} and node.args
                        and len(node.args) > 1 and isinstance(node.args[1], ast.Name)
                        and node.args[1].id == "path"):
                    values.append(ast.literal_eval(node.args[0]))
                if isinstance(node.func.value, ast.Name) and node.func.value.id == "path" and node.func.attr in {"startswith", "endswith"}:
                    raise ValueError("Review prefix/suffix HTTP route: " + ast.unparse(node))
            for value in values:
                if isinstance(value, str) and value.startswith("/"):
                    routes.add(method.name[3:] + " " + value)
    return routes


def summary(node, key, notes):
    extra = notes["symbols"].get(key, "")
    original = documentation(ast.get_docstring(node) or "")
    if extra:
        return extra + ("\n\n源码补充：\n\n" + original if original else "")
    if original:
        return original
    name = node.name
    common = notes["common"].get(name)
    if common:
        return common
    raise ValueError(f"Missing API explanation: {key}")


def link_for(target, modules):
    parts = target.split(".")
    for end in range(len(parts), 0, -1):
        module = ".".join(parts[:end])
        if module in modules:
            return f"[{target}]({page_name(module)})"
    return f"`{target}` (外部/基类接口)"


def build(root: Path, revision: str, notes: dict, http_notes: dict) -> tuple[dict[str, str], dict]:
    paths = discover(root)
    modules = {module_name(p, root): (p, ast.parse(p.read_text())) for p in paths}
    unknown = set(modules) - set(notes["modules"])
    stale = set(notes["modules"]) - set(modules)
    if unknown or stale:
        raise ValueError(f"Review module descriptions: new={sorted(unknown)}, removed={sorted(stale)}")
    alias_maps = {module: imports(tree, module, path.name == "__init__.py")
                  for module, (path, tree) in modules.items()}

    def canonical(target):
        seen = set()
        while target not in seen:
            seen.add(target)
            owner, _, name = target.rpartition(".")
            next_target = alias_maps.get(owner, {}).get(name)
            if not next_target:
                return target
            target = next_target
        raise ValueError("Review circular public re-export: " + target)

    pages = {}
    inventory = {}
    files = {}
    for module, (path, tree) in modules.items():
        relative = path.relative_to(root).as_posix()
        files[relative] = digest(path.read_bytes())
        url = f"{REPOSITORY}/blob/{revision}/{relative}"
        rows = [f"# {module}", "", "[API 索引](../index.md) · [接口特性与边界](../features.md)", "",
                f"源码基线：[{relative}]({url})；签名由 AST 提取，不导入硬件依赖。", "",
                notes["modules"][module], "",
                "源码说明中的历史验证记录、迁移目标和旧示例不代表当前固件可用；"
                "应用入口、资源准入和接口可用性以本页补充及接口特性文档为准。", ""]
        module_doc = documentation(ast.get_docstring(tree) or "")
        if module_doc:
            rows += ["## 模块契约（源码）", "", module_doc, ""]
        aliases = imports(tree, module, path.name == "__init__.py")
        exports = exported(tree)
        defined = {n.name for n in tree.body if isinstance(n, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))}
        # Local imports in ordinary modules are implementation dependencies;
        # package __init__ and explicit __all__ define re-export surfaces.
        if path.name == "__init__.py" or exports is not None:
            chosen = {k: v for k, v in aliases.items() if not k.startswith("_")
                      and k not in defined and (exports is None or k in exports)}
            if chosen:
                rows += ["## 公开导出 / 别名", "", "| 导入名称 | 定义与完整说明 |", "| --- | --- |"]
                for name, target in sorted(chosen.items()):
                    target = canonical(target)
                    rows.append(f"| `{name}` | {link_for(target, modules)} |")
                    inventory[module + "." + name] = {"kind": "export", "target": target}
                rows.append("")
        constants = [(n, item, doc) for n, item, doc in assignments(tree.body)
                     if n not in {"log", "logger"}]
        if constants:
            rows += ["## 常量与类型别名", "", "以下为该版本源码值；默认地址不等于所有固件都开放该服务。", ""]
            for name, item, doc in constants:
                rows += ["```python", declaration(item), "```", doc, ""]
                inventory[module + "." + name] = {"kind": "value", "declaration": declaration(item)}
        local_classes = {n.name: n for n in tree.body if isinstance(n, ast.ClassDef)}

        def methods(cls, seen=()):
            found = {}
            for base in cls.bases:
                if isinstance(base, ast.Name) and base.id in local_classes and base.id not in seen:
                    found.update(methods(local_classes[base.id], (*seen, cls.name)))
            for item in cls.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and public(item.name):
                    suffix = ".setter" if any(isinstance(d, ast.Attribute) and d.attr == "setter" for d in item.decorator_list) else ""
                    found[item.name + suffix] = (item, cls.name)
            return found

        def render_function(item, key, level, inherited=None):
            rows.extend(["#" * level + " " + key, "", "```python", declaration(item), "```", ""])
            explanation_key = module + "." + inherited + "." + item.name if inherited else key
            rows.extend([summary(item, explanation_key, notes), ""])
            if inherited:
                rows.extend([f"此方法定义于基类 `{inherited}`。", ""])
            rows.extend([f"[实现与参数校验]({url}#L{item.lineno})", ""])
            inventory[key] = {"kind": "callable", "declaration": declaration(item)}

        for node in tree.body:
            if not isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) or not public(node.name):
                continue
            key = module + "." + node.name
            if not isinstance(node, ast.ClassDef):
                render_function(node, key, 2)
                continue
            rows += [f"## {key}", "", "```python", declaration(node), "```", "", summary(node, key, notes), ""]
            inventory[key] = {"kind": "class", "declaration": declaration(node)}
            fields = list(assignments(node.body))
            ctypes_fields = next((n.value for n in node.body if isinstance(n, ast.Assign)
                                  and any(isinstance(t, ast.Name) and t.id == "_fields_" for t in n.targets)), None)
            if ctypes_fields:
                rows += ["### C 结构字段", "", "```python", "_fields_ = " + ast.unparse(ctypes_fields), "```", ""]
                inventory[key]["ctypes_fields"] = ast.unparse(ctypes_fields)
            if fields:
                rows += ["### 字段 / 默认值", "", "`@dataclass` 未显式定义构造器时，由下列字段生成；无默认值的字段必填。", "", "```python"]
                rows += [declaration(item) for _, item, _ in fields]
                rows += ["```", ""]
                for name, item, doc in fields:
                    inventory[key + "." + name] = {"kind": "field", "declaration": declaration(item)}
                    if doc:
                        rows += [f"`{name}`：{doc}", ""]
            for base in node.bases:
                base_name = ast.unparse(base)
                if base_name in aliases:
                    rows += ["继承接口：" + link_for(canonical(aliases[base_name]), modules) + "。", ""]
            for name, (item, owner) in methods(node).items():
                render_function(item, key + "." + name, 3, owner if owner != node.name else None)
        pages["python/" + page_name(module)] = "\n".join(rows).rstrip() + "\n"
        if exports is not None:
            missing = sorted(name for name in exports if module + "." + name not in inventory)
            if missing:
                raise ValueError(f"Review undocumented exports in {module}: {missing}")
    for name, spec in inventory.items():
        if spec["kind"] == "export" and spec["target"] not in inventory and spec["target"] not in modules:
            raise ValueError(f"Review unresolved public export: {name} -> {spec['target']}")
    for relative in EXTRA_SOURCES:
        path = root / relative
        files[relative] = digest(path.read_bytes())
    header = (root / "sdk/include/recamera_ext.h").read_text()
    pages["c-abi.md"] = ("# Native C ABI\n\n[API 索引](index.md) · [调用边界](features.md#native-and-platform)\n\n"
        "本文件保留该版本完整公开头文件及原始参数、错误码、字段、生命周期说明。\n"
        "Python 应用优先使用绑定；`osd`/`record` 入口仅限 AppMgr，不能以导出符号的存在推断应用调用权限。\n\n"
        f"源码基线：`{revision}`，`sdk/include/recamera_ext.h`。\n\n"
        "原始授权声明：[SDK NOTICE 与 BSD-3-Clause 许可证](sdk-license.txt)。\n\n```c\n" + header.rstrip() + "\n```\n")
    pages["sdk-license.txt"] = ((root / "sdk/NOTICE").read_text().rstrip() + "\n\n"
                                 + (root / "sdk/LICENSE").read_text())
    routes = http_routes((root / "market/appmgr/server.py").read_text())
    if routes != set(http_notes):
        raise ValueError(f"Review HTTP routes: new={sorted(routes - set(http_notes))}, removed={sorted(set(http_notes) - routes)}")
    http_rows = ["# App Center HTTP routes", "", "[API 索引](index.md) · [鉴权、响应和 WS 契约](http.md)", "",
                 "覆盖 server.py 的所有 HTTP 路由分支；带可选后缀/多个 action 的分支在说明中逐项展开。",
                 "`app_id` 为 `[a-z0-9-]{1,64}`，task/upload id 为 32 位小写十六进制；builtin 仅在明确允许的接口适用。", ""]
    for route in sorted(routes):
        spec = http_notes[route]
        if not all(isinstance(spec.get(k), str) and spec[k].strip() for k in ("path", "request", "response", "features")):
            raise ValueError("Incomplete HTTP explanation: " + route)
        http_rows += [f"## {route.split(' ', 1)[0]} {spec['path']}", "",
                      f"- 请求：{spec['request']}", f"- 返回：{spec['response']}",
                      f"- 特性：{spec['features']}", "", f"源码路由：`{route}`", ""]
    pages["http-routes.md"] = "\n".join(http_rows)
    index = ["# Public API reference", "", "Read only the modules needed for the task. These references work offline.", "",
             f"SDK source revision: `{revision}`. The builder is pinned separately by `sdk-contract-lock.json`.", "",
             "Start with [interface characteristics and limitations](features.md).", "",
             "Module descriptions and source docstrings retain their imported upstream language and attribution.", "",
             "| Python module | Imported description |", "| --- | --- |"]
    for module in modules:
        short = notes["modules"][module].split("\n", 1)[0].replace("|", "\\|")
        index.append(f"| [{module}](python/{page_name(module)}) | {short} |")
    index += ["", "Other public interfaces:", "", "- [Complete C ABI](c-abi.md)",
              "- [HTTP, SSE, WebSocket and platform interfaces](http.md)", "",
              "## Coverage", "",
              "The snapshot covers public definitions, exports, constructors, properties, fields, enums and local inherited methods in non-private `recamera_ext` and `kit` modules. Cross-module inheritance links to its owner.",
              "Compatibility and platform-only APIs remain documented with their caller restrictions; tests, private modules, caches and example CLIs are excluded.",
              "Signatures, annotations, defaults and original docstrings are extracted from AST without importing hardware dependencies. An absent annotation does not establish return semantics.",
              "Historical examples are context only. Managed entry, resource admission and result routing follow `features.md` and `managed-runtime.md`.",
              "API presence does not establish deployed firmware support, model accuracy, throughput or physical acceptance.", "",
              "## Repository maintenance", "",
              "The generator and editorial notes belong to the hardware repository's `tools/skill_packages/recamera/`, outside this installed Skill.", "",
              "From that repository, compare a compatible checkout with:", "", "```text",
              "python3 codecraft.py skill-reference --skill codecraft-development-recamera-pysdk --sdk-root <checkout> --check", "```", "",
              "This checks module/source inventories, public signatures, HTTP routes and generated pages. Review source changes before `--write --revision <full-commit>`; regeneration never changes the builder pin.", ""]
    pages["index.md"] = "\n".join(index)
    snapshot = {"source_revision": revision, "repository": REPOSITORY,
                "source_files": files, "symbols": inventory,
                "http_routes": sorted(routes),
                "generated_files": {name: digest(text.encode()) for name, text in sorted(pages.items())}}
    return pages, snapshot


def reference(root: Path, sdk_root: Path, *, write: bool = False, revision: str | None = None) -> dict:
    """Compare or regenerate references through the repository public entry."""
    root = Path(root).resolve()
    sdk_root = Path(sdk_root).expanduser().resolve()
    skill = root / "skills" / SKILL_ID
    destination = skill / "references/api"
    lock = skill / "scripts/api-reference-lock.json"
    maintenance = root / "tools/skill_packages/recamera"
    previous = read_json(lock)
    selected = revision or previous.get("source_revision")
    require(isinstance(selected, str) and re.fullmatch(r"[0-9a-f]{40}", selected),
            "Provide an explicit full source commit with --revision")
    if write:
        require(revision is not None, "Reference writes require an explicit --revision")
        def git(*args):
            return subprocess.run(["git", "-C", str(sdk_root), *args], check=True,
                                  capture_output=True, text=True, timeout=15).stdout.strip()
        try:
            require(Path(git("rev-parse", "--show-toplevel")).resolve() == sdk_root,
                    "The SDK root must be the checkout root")
            require(git("rev-parse", "HEAD") == selected, "SDK checkout differs from --revision")
            require(not git("status", "--porcelain", "--untracked-files=all"),
                    "Reference writes require a clean SDK checkout")
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            raise ValueError("Cannot verify the SDK checkout revision") from exc
    try:
        pages, snapshot = build(sdk_root, selected, read_json(maintenance / "api-notes.json"),
                                read_json(maintenance / "api-http-notes.json"))
    except SyntaxError as exc:
        raise ValueError(f"SDK source parsing failed: {exc}") from exc
    changed = sorted(name for name, content in pages.items()
                     if not (destination / name).is_file() or (destination / name).read_text() != content)
    source_changes = sorted(name for name in set(previous.get("source_files", {})) | set(snapshot["source_files"])
                            if previous.get("source_files", {}).get(name) != snapshot["source_files"].get(name))
    if write:
        for name in set(previous.get("generated_files", {})) - set(pages):
            safe_path(destination, name, exists=False).unlink(missing_ok=True)
        for name, content in pages.items():
            path = safe_path(destination, name, exists=False)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        lock.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    ok = write or previous == snapshot and not changed
    return {"status": "passed" if ok else "failed", "modules": len(discover(sdk_root)),
            "symbols": len(snapshot["symbols"]), "pages": len(pages),
            "changed_pages": changed, "source_changes": source_changes,
            "repository_changed": write and (previous != snapshot or bool(changed)),
            "source_revision": selected, "sdk_execution": "not_run"}
