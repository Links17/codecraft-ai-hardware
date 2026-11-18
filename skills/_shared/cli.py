"""CodeCraft hardware catalog, discovery, generation and evidence gate."""
from __future__ import annotations

import argparse
import ast
from datetime import datetime, timezone
import importlib.util
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from urllib.parse import unquote

from io_utils import ContractError, digest, read_json, require, source_files, object_digest, result
from runtime import run_target, load_adapter, check_envelope, exit_code
from model import Catalog, load_cloud
from project import generate_project, package_project, verify_project, lock_project, build_project
from render import generate, matrix
from evidence import validate_evidence
from testing import inventory as test_inventory, run_tests

ROOT = Path(__file__).resolve().parents[2]


def check_documentation(root):
    """Enforce README-only translations and resolve every local Markdown link."""
    for entry in source_files(root):
        if entry.suffix != '.md':
            continue
        relative = entry.relative_to(root).as_posix()
        require(not entry.name.endswith('.zh_CN.md') or entry.name == 'README.zh_CN.md',
                f'{relative}: only README may have a Chinese counterpart')
        if entry.name == 'README.md':
            translated = entry.with_name('README.zh_CN.md')
            require(translated.is_file(), f'{relative}: missing README Chinese counterpart')
            require('README.zh_CN.md' in entry.read_text() and 'README.md' in translated.read_text(),
                    f'{relative}: missing reciprocal README links')
        elif entry.name == 'README.zh_CN.md':
            require(entry.with_name('README.md').is_file(), f'{relative}: orphan Chinese README')
        for match in re.findall(r'\]\(([^)]+)\)|href="([^"]+)"',entry.read_text()):
            link=next(x for x in match if x).split('#')[0]
            if not link or '://' in link or link.startswith(('mailto:','data:')) or any(x in link for x in '<> '):
                continue
            require((entry.parent/unquote(link)).exists(),f'{relative}: broken local link {link}')


def static_checks(c):
    checks = []
    ast.parse((c.root/'codecraft.py').read_text(),filename='codecraft.py')
    c.cloud()
    checks.append(result('cloud-capabilities/contracts-and-provider-references','passed'))
    checks.extend(c.cloud().check_skills())
    for t in c.targets.values():
        load_adapter(c.root, c.platforms[t['platform']]).validate_target(c.root, t)
        checks.append(result(t['id']+'/contract', 'passed'))
    for pattern in ('devices/*/device.json', 'platforms/*/platform.json', 'platforms/*/targets/*/target.json', 'capabilities/*/capability.json'):
        for path in c.root.glob(pattern):
            canonical=json.dumps(read_json(path),ensure_ascii=False,indent=2,sort_keys=True)+'\n'
            require(path.read_text()==canonical,f'{path}: noncanonical metadata formatting')
    for area in ('skills','platforms','capabilities','devices'):
        for path in source_files(c.root/area):
            if path.suffix=='.py':
                ast.parse(path.read_text(),filename=str(path))
    require('Apache License' in (c.root/'LICENSE').read_text() and (c.root/'NOTICE').read_text().strip(), 'Repository license/attribution missing')
    for path in c.root.glob('platforms/*/components/*'):
        if path.is_dir():
            texts=[p.read_text(errors='replace') for p in source_files(path) if p.suffix in ('.h','.c','.md','.txt')]
            require(any('Copyright' in text or 'SPDX-License-Identifier' in text or 'Apache License' in text for text in texts), f'{path}: component attribution missing')
    checks += [result('source/format-and-python-syntax','passed'),result('source/licenses-and-attribution','passed')]
    # Engineering entry points are required once, in English.
    entries = [c.root/'AGENTS.md', c.root/'README.md', c.root/'CLAUDE.md', c.root/'devices/AGENTS.md', c.root/'capabilities/AGENTS.md', c.root/'platforms/AGENTS.md']
    entries += list(c.root.glob('devices/*/AGENTS.md')) + list(c.root.glob('platforms/*/AGENTS.md'))
    entries += list(c.root.glob('skills/*/SKILL.md')) + list(c.root.glob('capabilities/*/AGENTS.md'))
    for entry in entries:
        require(entry.is_file(), f'{entry}: missing required documentation entry')
    check_documentation(c.root)
    for device in c.devices.values():
        for tid in c.device_targets(device['id']):
            c.context(tid)
            c.support(tid)
    drift = generate(c, check=True)
    require(not drift, 'generated files are stale: '+', '.join(drift))
    # Scan source files and untracked additions too; split the pattern so this
    # validator's own source is not mistaken for a private key.
    key = re.compile('-----BEGIN '+'(?:RSA |EC |OPENSSH )?PRIVATE KEY-----')
    for area in ('devices','platforms','capabilities','skills','docs','.github'):
        for path in source_files(c.root/area):
            if path.suffix in ('.md','.py','.c','.h','.json','.yml','.yaml','.sh'):
                require(not key.search(path.read_text(errors='replace')), f'private-key material in {path.relative_to(c.root)}')
    checks += [result('knowledge/closure','passed'), result('generated/check','passed'), result('documentation/language-and-links','passed'), result('source/private-keys','passed')]
    return checks


def target_receipt(c, tid):
    target=c.target(tid)
    adapter=load_adapter(c.root,c.platforms[target['platform']])
    return {'source_digest':c.graph(tid).fingerprint(),'toolchain':adapter.probe(c.root,target),'expected_cases':adapter.cases(c.root,target)}


def validate_project(c, tid, variant=None):
    """Build the selected example in a clean external directory via its public entry."""
    target=c.target(tid)
    example=target['examples'][0]
    if target.get('variants') and variant is None:
        projects={name:validate_project(c,tid,name) for name in target['variants']}
        status='passed' if all(item['status']=='passed' for item in projects.values()) else ('failed' if any(item['status']=='failed' for item in projects.values()) else 'not_run')
        log=c.root/'.codecraft/logs'/('generated_'+tid.replace('/','_')+'.log')
        log.write_text('\n'.join(name+'\n'+(c.root/item['log']).read_text() for name,item in projects.items()))
        return result(tid+'/generated-project',status,'Clean locked exports cover every registered variant.',
                      kind='variant-project-set',example=example,variant_projects=projects,
                      source_digest=object_digest({name:item.get('source_digest') for name,item in projects.items()}),
                      origin_source_digest=c.graph(tid).fingerprint(),log=str(log.relative_to(c.root)),log_sha256=digest(log),
                      build_results=[row for item in projects.values() for row in item.get('build_results',[])],
                      provenance='passed' if all(item.get('provenance')=='passed' for item in projects.values()) else 'failed',
                      toolchain=projects[target['default_variant']].get('toolchain'))
    with tempfile.TemporaryDirectory(prefix='codecraft-generated-check-') as folder:
        output=Path(folder)/'project'
        log=c.root/'.codecraft/logs'/('generated_'+tid.replace('/','_')+('_'+variant if variant is not None else '')+'.log')
        log.parent.mkdir(parents=True,exist_ok=True)
        log.write_text('')
        try:
            generated=generate_project(c,tid,example,output,variant=variant)
            require(verify_project(output)['status']=='passed','fresh project lock mismatch')
            check_documentation(output)
            run=subprocess.run([sys.executable,str(output/'codecraft.py'),'build-project','.'],cwd=output,capture_output=True,text=True,timeout=1900)
            transcript=run.stdout+'\n'+run.stderr
            for child in sorted((output/'.codecraft/logs').glob('*.log')):
                transcript+='\n'+child.name+'\n'+child.read_text(errors='replace')
            log.write_text(transcript)
            response=json.loads(run.stdout)
            require(response.get('schema_version') == 2 and type(response.get('ok')) is bool and isinstance(response.get('data'), dict), 'Invalid public CLI build response')
            payload=response['data']
            require(response['ok'] == payload.get('ok'), 'Public CLI and native build status differ')
            imported=Catalog(output)
            native=load_adapter(output,imported.platforms[target['platform']])
            checks=check_envelope(payload,tid,'build',imported.graph(tid).fingerprint(),native.cases(output,imported.target(tid),example),run.returncode)
            provenance=verify_project(output)
            passed=all(item['status']=='passed' for item in checks) and provenance['status']=='passed'
            status='passed' if passed else ('failed' if provenance['drift'] or any(item['status']=='failed' for item in checks) else 'not_run')
            return result(tid+'/generated-project',status,'Clean external import, locked environment, native build and provenance check.',example=example,
                          source_digest=generated['source_digest'],origin_source_digest=generated['origin_source_digest'],variant=generated.get('variant'),
                          log=str(log.relative_to(c.root)),log_sha256=digest(log),build_results=checks,provenance=provenance['status'],toolchain=payload['resolved_toolchain'])
        except (ValueError,KeyError,TypeError,ContractError,OSError,subprocess.TimeoutExpired) as exc:
            with log.open('a') as output_log:
                output_log.write(f'\n{type(exc).__name__}: {exc}\n')
            return result(tid+'/generated-project','failed',str(exc),log=str(log.relative_to(c.root)),log_sha256=digest(log))


def record_evidence(c,source):
    record=read_json(source)
    t=validate_evidence(c,record,current=True)
    commit=subprocess.run(['git','cat-file','-e',record['repository_commit']+'^{commit}'],cwd=c.root,capture_output=True)
    require(commit.returncode==0,'repository_commit does not exist in this repository')
    identity=hashlib.sha256(json.dumps(record,sort_keys=True).encode()).hexdigest()[:16]
    out=c.root/'devices'/t['device']/'tests/records'/f'{record["kind"]}-{identity}.json'
    require(not out.exists(),'evidence record exists; do not overwrite prior observations')
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
    return {'path':str(out.relative_to(c.root)),'result':record['result']}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT)
    sub=parser.add_subparsers(dest='command',required=True)
    sub.add_parser('catalog')
    sub.add_parser('cloud-catalog')
    external=sub.add_parser('check-cloud-skills');external.add_argument('--skills-root',type=Path,help='Installed Skill parent; defaults to this repository’s skills directory')
    resolve=sub.add_parser('resolve-capability');resolve.add_argument('--capability',required=True);resolve.add_argument('--target',help='Optional hardware context; cloud Skills run on the Agent host');resolve.add_argument('--requirements',type=Path)
    prepare=sub.add_parser('prepare-capability');prepare.add_argument('--selection',type=Path,required=True);prepare.add_argument('--target',help='Optional hardware context');prepare.add_argument('--operation',required=True);prepare.add_argument('--input',type=Path,required=True)
    inspect=sub.add_parser('context');inspect.add_argument('--target',required=True);inspect.add_argument('--example');inspect.add_argument('--task',default='develop');inspect.add_argument('--provider',action='append',default=[])
    inspect.add_argument('--variant',help='Declared hardware build variant; physical revision remains separate')
    discover=sub.add_parser('discover');discover.add_argument('--interface',action='append',default=[]);discover.add_argument('--platform');discover.add_argument('--constraints',type=Path)
    gen=sub.add_parser('generate');gen.add_argument('--check',action='store_true')
    sub.add_parser('matrix')
    val=sub.add_parser('validate');val.add_argument('--static',action='store_true');val.add_argument('--target');val.add_argument('--example');val.add_argument('--projects',action='store_true');val.add_argument('--report',type=Path)
    val.add_argument('--variant',help='Build one declared variant; the full gate builds all registered variants')
    tests=sub.add_parser('test',help='List or run host tests at their owning paths')
    tests.add_argument('--path',help='Repository-relative test file or owning directory')
    tests.add_argument('--list',action='store_true',help='Collect test IDs without executing test bodies')
    new=sub.add_parser('new');new.add_argument('--target',required=True);new.add_argument('--example',required=True);new.add_argument('--output',type=Path,required=True);new.add_argument('--capabilities',type=Path)
    new.add_argument('--variant',help='Explicit variant selection; otherwise use the declared build default')
    verify=sub.add_parser('verify-project');verify.add_argument('path',type=Path)
    refresh=sub.add_parser('lock-project');refresh.add_argument('path',type=Path)
    build=sub.add_parser('build-project');build.add_argument('path',type=Path)
    pack=sub.add_parser('package');pack.add_argument('path',type=Path);pack.add_argument('--output',type=Path,required=True)
    evidence=sub.add_parser('record-evidence');evidence.add_argument('--file',type=Path,required=True)
    release=sub.add_parser('skill-release',help='Prepare, check or explicitly apply standalone Skill candidates')
    release.add_argument('release_args',nargs=argparse.REMAINDER)
    args=parser.parse_args(argv)
    try:
        if args.command=='test':
            if args.list:
                data=test_inventory(args.root,selection=args.path)
                code=1 if data['collection_errors'] else 0
            else:
                checks=run_tests(args.root,selection=args.path)
                data={'results':checks,'scope':'host-only','device_verification':'not_run','api_execution':'not_run'}
                code=exit_code(checks)
            print(json.dumps({'schema_version':2,'ok':code==0,'data':data},ensure_ascii=False,indent=2))
            return code
        if args.command=='skill-release':
            path=args.root/'skills/_cloud/release.py'
            if not path.is_file():
                require((args.root/'project.yaml').is_file() and (args.root/'codecraft.lock').is_file(),
                        'Missing repository Skill release implementation; restore the maintained source before retrying.')
                print(json.dumps({'schema_version':2,'ok':False,'data':{'status':'not_supported','reason':'Skill release maintenance requires the full repository; it is not exported into applications.'}}))
                return 2
            spec=importlib.util.spec_from_file_location('codecraft_skill_release',path)
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            return module.main(args.release_args,root=args.root)
        cloud_command=args.command in ('cloud-catalog','check-cloud-skills','resolve-capability','prepare-capability')
        c=load_cloud(args.root) if cloud_command else Catalog(args.root)
        data={};ok=True;code=0
        if args.command=='catalog':data={'devices':c.devices,'platforms':c.platforms,'targets':c.targets,'capabilities':c.capabilities}
        elif args.command=='cloud-catalog':data=c.describe()
        elif args.command=='check-cloud-skills':
            data={'results':c.check_skills(args.skills_root),'api_execution':'not_run'};ok=all(item['status']=='passed' for item in data['results'])
        elif args.command=='resolve-capability':
            requirements=read_json(args.requirements) if args.requirements else {}
            require(isinstance(requirements,dict) and set(requirements)<={'environment','limits'},'Requirements must be an object with environment and/or limits')
            data=c.resolve(args.capability,args.target,requirements.get('environment'),requirements.get('limits'))
        elif args.command=='prepare-capability':data=c.prepare(read_json(args.selection),args.target,args.operation,read_json(args.input))
        elif args.command=='context':data=c.context(args.target,args.example,args.task,args.provider,variant=args.variant)
        elif args.command=='discover':data=c.resolve(args.interface,args.platform,read_json(args.constraints) if args.constraints else None)
        elif args.command=='matrix':data=matrix(c)
        elif args.command=='generate':
            changed=generate(c,args.check);data={'changed':changed,'check':args.check};ok=not args.check or not changed
        elif args.command=='new':
            selections=read_json(args.capabilities) if args.capabilities else []
            require(isinstance(selections,list),'Capability selections must be a list')
            data=generate_project(c,args.target,args.example,args.output,selections,variant=args.variant)
        elif args.command=='lock-project':data=lock_project(args.path)
        elif args.command=='build-project':
            data=build_project(args.path);ok=data['ok'];code=exit_code(data['results'])
        elif args.command=='verify-project':data=verify_project(args.path);ok=data['status']=='passed'
        elif args.command=='package':data=package_project(args.path,args.output)
        elif args.command=='record-evidence':data=record_evidence(c,args.file)
        elif args.command=='validate':
            require(not(args.static and args.target),'choose --static or --target')
            require(not args.example or args.target,'--example requires --target')
            require(not args.variant or args.target,'--variant requires --target')
            checks=[]
            receipts={}
            if args.target:
                receipts[args.target]=target_receipt(c,args.target)
                checks=run_target(c,args.target,args.example,args.variant)
                if args.projects:
                    checks.append(validate_project(c,args.target,args.variant))
            else:
                checks=static_checks(c)+run_tests(c.root)
                if not args.static and all(x['status']=='passed' for x in checks):
                    for tid in c.targets:
                        receipts[tid]=target_receipt(c,tid)
                        checks+=run_target(c,tid)
                        checks.append(validate_project(c,tid))
            ok=all(x['status']=='passed' for x in checks)
            code=1 if any(x['status']=='failed' for x in checks) else (0 if ok else 2)
            data={'scope':'static+host' if args.static else (args.target or 'complete-software-gate'),'results':checks,'device_verification':'not_run','generated_at':datetime.now(timezone.utc).isoformat(),'targets':receipts,'simulation':{pid:p['operations']['simulate'] for pid,p in c.platforms.items()}}
            if args.report:
                args.report.parent.mkdir(parents=True,exist_ok=True)
                args.report.write_text(json.dumps({'schema_version':2,'ok':ok,'data':data},ensure_ascii=False,indent=2)+'\n')
        print(json.dumps({'schema_version':2,'ok':ok,'data':data},ensure_ascii=False,indent=2))
        return code or (0 if ok else 1)
    except (ContractError,OSError,ValueError,KeyError,TypeError) as exc:
        print(json.dumps({'schema_version':2,'ok':False,'error':{'type':'contract','message':str(exc)}},ensure_ascii=False))
        return 1

