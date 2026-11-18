"""Cloud Skill discovery and dry-run handoff; clients live in standalone Skills."""
import copy
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from graph import SourceGraph
from io_utils import digest, object_digest, require, safe_path
from registry import domain, load_group


class CapabilityCatalog:
    def __init__(self, root, target_lookup=None):
        self.root=Path(root).resolve();self._target_lookup=target_lookup
        self.schema=domain(self.root,'capabilities')
        self.capabilities=load_group(self.root,'capabilities/*/capability.json')
        self.providers=load_group(self.root,'capabilities/*/providers/*/provider.json')
        self.models=load_group(self.root,'capabilities/*/models/*/model.json')
        for path in (self.root/'capabilities').iterdir():
            if path.is_dir() and not path.name.startswith(('.', '_')):
                require((path/'capability.json').is_file(),f'Unregistered Capability directory: {path.name}')
        for cid,cap in self.capabilities.items():
            require((self.root/'capabilities'/cid/'capability.json').is_file(),'Capability identity/path mismatch')
            self.schema.validate(self.root,cap)
        for pid,p in self.providers.items():
            require(p.get('capability') in self.capabilities,'Unknown Provider Capability')
            self.schema.provider(self.root,p,self.capabilities[p['capability']])
            require((self.root/'capabilities'/p['capability']/'providers'/pid.split('/')[1]/'provider.json').is_file(),'Provider path mismatch')
            require(set(p['models'])<=self.models.keys(),'Unknown Provider Model Artifact')
            self.graph(pid)
        for artifact in self.models.values():self.schema.model(self.root,artifact)

    def describe(self):
        return {'capabilities':[{'id':cid,'version':cap['version'],'consumer':cap['consumer'],'description':cap['description'],
                                'providers':sorted(pid for pid,p in self.providers.items() if p['capability']==cid),
                                'route':cap['agent_route'],'execution':'not_run'} for cid,cap in sorted(self.capabilities.items())],
                'providers':self.providers,'models':self.models}

    def graph(self,pid):
        require(pid in self.providers,'Unknown Provider')
        p=self.providers[pid];cid=p['capability'];cap=self.capabilities[cid]
        roots=['capabilities/schema.py','capabilities/catalog.py',
               'skills/_shared/registry.py','skills/_shared/graph.py','skills/_shared/io_utils.py',
               'docs/architecture/capability-provider-policy.md',
               f'capabilities/{cid}/capability.json',
               f'capabilities/{cid}/providers/{pid.split("/")[1]}/provider.json',cap['agent_route'],
               *p['dependencies']]
        if p['kind']=='repository-skill':
            # Pinned package files are explicit inputs, including binary assets
            # that generic directory scans intentionally exclude.
            roots += [p['skill']['path']+'/'+relative for relative in p['skill']['files']]
        for mid in p['models']:
            model=self.models[mid]
            roots += [f'capabilities/{cid}/models/{mid.split("/")[-1]}/model.json',model['path']]
        graph=SourceGraph(self.root);graph.resolve(roots);return graph

    def resolve(self,cid,tid=None,environment=None,limits=None):
        require(cid in self.capabilities,'Unknown Capability')
        if tid is not None:
            require(self._target_lookup is not None,
                    'Explicit Target context requires a caller-supplied Target resolver')
            self._target_lookup(tid)
        environment={} if environment is None else environment
        limits={} if limits is None else limits
        require(isinstance(environment,dict) and isinstance(limits,dict),'Environment and limits must be objects')
        require(set(environment)<={'network','tls','loopback','secret_refs','environment_refs','privacy_approved'},'Unknown environment field; never supply credential values')
        for name in ('network','tls','loopback','privacy_approved'):
            require(name not in environment or type(environment[name]) is bool,'Environment decisions must be booleans')
        for name in ('secret_refs','environment_refs'):
            require(name not in environment or isinstance(environment[name],list) and all(isinstance(value,str) for value in environment[name]),'Environment references must be lists of names')
        require(set(limits)<=self.capabilities[cid]['resources'].keys(),'Unknown resource constraint')
        require(all(type(v) is int and v>=0 for v in limits.values()),'Invalid resource limit')
        candidates=[];rejected=[]
        for pid,p in sorted(self.providers.items()):
            if p['capability']!=cid:continue
            unknown=[];conflicts=[];pre=p['prerequisites']
            for key in ('network','tls'):
                if key=='tls' and pre.get('loopback_http') and environment.get('loopback') is True:
                    continue
                if pre[key] and environment.get(key) is False:conflicts.append(key+' is required')
                elif pre[key] and environment.get(key) is not True:unknown.append(key+' availability is unknown')
            if pre['privacy']!='no external data' and environment.get('privacy_approved') is not True:unknown.append('Data processing/privacy decision is required')
            for key in ('secret_refs','environment_refs'):
                if not set(pre[key])<=set(environment.get(key,[])):unknown.append('Required '+key+' are not configured')
            for key,maximum in limits.items():
                if p['resources'][key] is None:unknown.append(key+' bound is unknown')
                elif p['resources'][key]>maximum:conflicts.append(key+' exceeds the limit')
            item={'provider':pid,'target':tid,'status':'unsupported' if conflicts else ('unknown' if unknown else 'eligible'),
                  'unknowns':unknown,'conflicts':conflicts,'execution':'not_run','device_integration':'unknown','limitations':p['limitations'],
                  'contract_limits':copy.deepcopy(self.capabilities[cid]['limits']),
                  'provider_policy':copy.deepcopy(p['policy'])}
            (rejected if conflicts else candidates).append(item)
        registered=any(p['capability']==cid for p in self.providers.values())
        return {'capability':cid,'target':tid,'candidates':candidates,'rejected':rejected,
                'status':'candidates' if candidates else ('unsupported' if registered else 'unknown'),
                'reason':'' if candidates else ('No eligible Provider.' if registered else 'No Provider is registered.'),
                'needs_user_input':len(candidates)!=1 or bool(candidates and candidates[0]['status']!='eligible')}

    def selection(self,item,tid=None):
        require(isinstance(item,dict) and set(item)=={'capability','provider','configuration','environment','limits'},'Selection requires Capability, Provider, configuration, environment and limits')
        cid=item['capability'];pid=item['provider']
        require(cid in self.capabilities and pid in self.providers and self.providers[pid]['capability']==cid,'Unknown Capability/Provider selection')
        provider=self.providers[pid]
        effective=self.schema.policy(provider,self.capabilities[cid])
        require(isinstance(item['configuration'],dict),'configuration must be an object')
        configuration={**provider['policy']['defaults'],**item['configuration']}
        self.schema.payload(effective['configuration'],configuration,'configuration')
        resolved=self.resolve(cid,tid,item['environment'],item['limits'])
        chosen=next((x for x in resolved['candidates'] if x['provider']==pid),None)
        require(chosen and chosen['status']=='eligible','Provider selection is unsupported or unresolved: '+str(resolved))
        return {'capability':cid,'contract_version':self.capabilities[cid]['version'],'provider':pid,
                'configuration':item['configuration'],'secret_refs':self.providers[pid]['prerequisites']['secret_refs'],
                'effective_configuration':configuration,'provider_policy':copy.deepcopy(provider['policy']),
                'contract_limits':copy.deepcopy(self.capabilities[cid]['limits']),
                'source_digest':self.graph(pid).fingerprint(),'skill':self.providers[pid]['skill'],
                'skill_kind':self.providers[pid]['kind'],'execution':'not_run'}

    def prepare(self,item,tid,operation,value):
        selection=self.selection(item,tid);cap=self.capabilities[item['capability']];p=self.providers[item['provider']]
        require(operation in p['operations'],'Unknown Provider operation')
        effective=self.schema.policy(p,cap)
        self.schema.payload(effective['operations'][operation]['input'],value,'input')
        mapping=p['operations'][operation];args=list(mapping.get('fixed_arguments',[]))
        for data,flags in [(value,mapping['arguments']),(selection['effective_configuration'],mapping['options'])]:
            for key,val in data.items():
                if type(val) is bool:
                    if val:args.append(flags[key])
                else:args += [flags[key],str(val)]
        return {'schema_version':2,'consumer':'cloud-skill','target':tid,**selection,'operation':operation,
                'entrypoint':{'skill':p['skill']['id'],'path':p['skill']['entrypoint']},'arguments':args,
                'required_environment':p['prerequisites']['environment_refs']+p['prerequisites']['secret_refs'],
                'input_schema':effective['operations'][operation]['input'],
                'configuration_schema':effective['configuration'],
                'output_schema':effective['operations'][operation]['output'],'execution':'not_run',
                'reason':'Handoff only. Run the existing installed Skill solely for an explicitly authorized cloud operation.'}

    def check_skills(self,skills_root=None):
        root=Path(skills_root or self.root/'skills').expanduser().resolve();checks=[]
        for pid,p in sorted(self.providers.items()):
            # An external-only registration has no repository package to inspect.
            if skills_root is None and p['kind']=='external-skill':
                continue
            skill=p['skill']
            package=safe_path(root,skill['id'],exists=False)
            actual=self.schema.package_inventory(package) if package.is_dir() else {}
            drift=sorted(name for name in actual.keys() | skill['files'].keys() if actual.get(name)!=skill['files'].get(name))
            if drift:
                checks.append({'name':pid,'status':'failed','reason':'Skill differs from pinned source','drift':drift})
                continue
            # Run only pinned bytes in a fresh directory: installed bytecode,
            # neighboring modules and PYTHONPATH are not validation inputs.
            with tempfile.TemporaryDirectory(prefix='codecraft-skill-check-') as folder:
                verified=Path(folder)/skill['id']
                for relative in skill['files']:
                    destination=verified/relative
                    destination.parent.mkdir(parents=True,exist_ok=True)
                    shutil.copy2(safe_path(package,relative),destination)
                path=verified/skill['entrypoint']
                run=subprocess.run([sys.executable,'-E','-s','-B',str(path),'--help'],cwd=folder,capture_output=True,text=True,timeout=30)
            flags={flag for op in p['operations'].values() for flag in [*op['arguments'].values(),*op['options'].values(),*op.get('fixed_arguments',[])]}
            valid=run.returncode==0 and all(flag in run.stdout for flag in flags)
            checks.append({'name':pid,'status':'passed' if valid else 'failed','reason':'Pinned package and offline CLI argument contract checked.' if valid else 'Skill CLI contract mismatch',
                           'source_digest':object_digest(skill['files']),'api_execution':'not_run'})
        return checks
