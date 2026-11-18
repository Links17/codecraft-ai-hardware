"""Catalog orchestration across Device, Platform and Capability domain contracts."""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

from io_utils import read_json, require, safe_path
from graph import SourceGraph
from registry import domain, load_group


def load_cloud(root, target_lookup=None):
    """Compose cloud contracts with lazy, optional hardware-context validation."""
    root = Path(root).resolve()
    path = root/'capabilities/catalog.py'
    require(path.is_file(), 'Cloud Capability support is not included in this project')
    spec = importlib.util.spec_from_file_location('cloud_capability_catalog', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if target_lookup is None:
        # Keep public CLI behavior here. The cloud domain neither imports nor
        # constructs a hardware Catalog, and no hardware is read without tid.
        def target_lookup(tid):
            return Catalog(root).target(tid)
    return module.CapabilityCatalog(root, target_lookup=target_lookup)


class Catalog:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.devices = load_group(self.root, 'devices/*/device.json')
        self.platforms = load_group(self.root, 'platforms/*/platform.json')
        self.targets = load_group(self.root, 'platforms/*/targets/*/target.json')
        self._cloud_cache = None
        self.device_schema = domain(self.root, 'devices')
        self.platform_schema = domain(self.root, 'platforms')
        require(self.devices and self.platforms and self.targets, 'empty catalog')
        self.check()

    def check(self):
        for area, manifest in [('devices', 'device.json'), ('platforms', 'platform.json')]:
            for path in (self.root/area).iterdir():
                if path.is_dir() and not path.name.startswith(('.', '_')):
                    require((path/manifest).is_file(), f'unregistered {area} directory: {path.name}')
        for path in self.root.glob('platforms/*/targets/*'):
            if path.is_dir() and not path.name.startswith('.'):
                require((path/'target.json').is_file(), f'unregistered Target: {path}')
        for identity, item in self.devices.items():
            require((self.root/'devices'/identity/'device.json').is_file(), 'Device identity/path mismatch')
            self.device_schema.validate(self.root, item)
        for identity, item in self.platforms.items():
            require((self.root/'platforms'/identity/'platform.json').is_file(), 'Platform identity/path mismatch')
            self.platform_schema.validate(self.root, item)
        for tid, target in self.targets.items():
            self.platform_schema.target(self.root, target, self.devices, self.platforms)
            self.graph(tid)
        require(all(self.device_targets(did) for did in self.devices), 'Device requires at least one Target')

    def cloud(self):
        if self._cloud_cache is None:
            self._cloud_cache = load_cloud(self.root, target_lookup=self.target)
        return self._cloud_cache

    @property
    def capabilities(self):
        return self.cloud().capabilities

    def device_targets(self, did):
        return sorted(tid for tid, target in self.targets.items() if target['device'] == did)

    def target(self, tid):
        require(tid in self.targets, f'unknown Target: {tid}')
        return self.targets[tid]

    def selected_target(self, tid, example=None, variant=None):
        target = copy.deepcopy(self.target(tid))
        variants = target.get('variants', {})
        if variant is not None or (example and variants):
            variant = variant if variant is not None else target['default_variant']
            require(variant in variants, f'{tid}: unknown variant {variant}')
            target['variants'] = {variant: variants[variant]}
            target['selected_variant'] = variant
            target['default_variant'] = variant
        if not example:
            return target
        require(example in target['examples'], f'{tid}: unknown example {example}')
        target['examples'] = [example]
        for key in ('example_inputs', 'example_dependencies'):
            target[key] = {example: target[key][example]}
        bindings = []
        for binding in target['interfaces']:
            scoped = binding.get('example_implementation', {})
            binding['example_implementation'] = {example: scoped[example]} if example in scoped else {}
            if not binding['implementation'] and not binding['example_implementation']:
                continue
            for operation in binding['operations'].values():
                if 'example_sources' in operation:
                    operation['example_sources'] = {example: operation['example_sources'][example]}
            bindings.append(binding)
        target['interfaces'] = bindings
        return target

    def graph(self, tid, example=None, variant=None):
        target = self.selected_target(tid, example, variant)
        device = self.devices[target['device']]
        platform = self.platforms[target['platform']]
        roots = [f'devices/{device["id"]}/device.json', f'{target["path"]}/target.json',
                 f'platforms/{platform["id"]}/platform.json', platform['adapter'],
                 *platform['runtime'], *device['references'], device['assets'],
                 f'devices/{device["id"]}/tests/acceptance.json',
                 *target['inputs'], *target['dependencies'], target['toolchain']['source']]
        for asset in read_json(self.root/device['assets'])['assets']:
            roots.append(asset['path'])
        for case in read_json(self.root/f'devices/{device["id"]}/tests/acceptance.json')['cases']:
            roots.append(case['source'])
        for name in target['examples']:
            roots += target['example_inputs'][name] + target['example_dependencies'][name]
        for choice in target.get('variants', {}).values():
            roots += choice['inputs'] + choice['dependencies']
        for binding in target['interfaces']:
            roots += binding['implementation']
            roots += [ref for refs in binding.get('example_implementation', {}).values() for ref in refs]
        graph = SourceGraph(self.root)
        graph.resolve(roots)
        profile = self.root/'project.yaml'
        if profile.is_file():
            selections = read_json(profile).get('capabilities', [])
            require(isinstance(selections, list), 'Capability selections must be a list')
            for selection in selections:
                require(isinstance(selection, dict) and isinstance(selection.get('provider'), str), 'Invalid Capability selection')
                graph.resolve(self.cloud().graph(selection['provider']).files)
        return graph

    def support(self, tid):
        from evidence import support
        return support(self, tid)

    def context(self, tid, example=None, task='develop', providers=(), variant=None):
        skills = {'ideate': ['codecraft-ideate', 'codecraft-discover'], 'develop': ['codecraft-develop'], 'setup': ['codecraft-setup'], 'build': ['codecraft-build'],
                  'debug': ['codecraft-debug'], 'device-test': ['codecraft-device-test'],
                  'discover': ['codecraft-discover'], 'validate': ['codecraft-validate']}
        require(task in skills, f'unknown context task: {task}')
        target = self.selected_target(tid, example, variant)
        graph = self.graph(tid, example, variant)
        for pid in providers:
            graph.resolve(self.cloud().graph(pid).files)
        guidance = ['AGENTS.md', f'devices/{target["device"]}/AGENTS.md', f'platforms/{target["platform"]}/AGENTS.md']
        guidance += [f'skills/{name}/SKILL.md' for name in skills[task]]
        for path in guidance:
            safe_path(self.root, path)
        return {'schema_version': 2, 'device': self.devices[target['device']], 'target': target, 'task': task,
                'files': sorted(graph.files | set(guidance)), 'dependencies': graph.snapshot()['edges'],
                'source_digest': graph.fingerprint(), 'support': self.support(tid), 'unknowns': self.devices[target['device']]['unknowns']}

    def resolve(self, interface_ids=(), platform=None, constraints=None):
        constraints = constraints or {}
        available = {entry['id'] for target in self.targets.values() for entry in target['interfaces']}
        require(set(interface_ids) | set(constraints) <= available, 'unknown requested native interface')
        require(platform is None or platform in self.platforms, 'unknown requested platform')
        requested = set(interface_ids) | set(constraints)
        candidates, rejected = [], []
        for tid, target in sorted(self.targets.items()):
            if platform and target['platform'] != platform:
                continue
            bindings = {binding['id']: binding for binding in target['interfaces']}
            if not requested <= bindings.keys():
                rejected.append({'target': tid, 'reason': 'Missing implementations', 'missing': sorted(requested - bindings.keys())})
                continue
            matches = {cid: self.platform_schema.match_interface(bindings[cid], constraints.get(cid, {})) for cid in requested}
            if any(item['status'] == 'unsupported' for item in matches.values()):
                rejected.append({'target': tid, 'constraints': matches})
                continue
            candidates.append({'target': tid, 'compatibility': 'unknown' if any(item['status'] == 'unknown' for item in matches.values()) else 'match',
                               'constraints': matches, 'verification': self.support(tid)['level'], 'unknowns': self.devices[target['device']]['unknowns']})
        return {'candidates': candidates, 'rejected': rejected, 'status': 'candidates' if candidates else 'unsupported',
                'needs_user_input': len(candidates) != 1, 'physical_compatibility': 'unknown'}
