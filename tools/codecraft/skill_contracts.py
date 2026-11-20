"""Skill-owned contract checks, selected package graphs and release inventories."""
import copy
import math
import re

from pathlib import Path

from io_utils import digest, localized, require, safe_path, read_json, object_digest
from graph import SourceGraph
from registry import load_group

NAME = r'[a-z0-9]+(?:-[a-z0-9]+)*'
VERSION = r'\d+\.\d+\.\d+'


def record_path(skill):
    require(isinstance(skill, str) and re.fullmatch(NAME, skill), 'Invalid Skill identity')
    return f'tools/skill_packages/packages/{skill}.json'


def registrations(root):
    """Read release records without accepting unreviewed package-byte changes."""
    records = load_group(Path(root), 'tools/skill_packages/packages/*.json')
    require(records, 'No standalone Skill packages registered')
    owners = {path.parent.name for path in Path(root).glob('skills/*/contract.json')}
    require(set(records)==owners, 'Skill contracts and release records must have exactly one matching owner')
    for sid, record in records.items():
        require(read_json(safe_path(root, record_path(sid))) == record, 'Skill release identity/path mismatch')
        require(record.get('schema_version') == 1 and type(record['schema_version']) is int,
                'Unsupported Skill release schema')
    return records


def validate_contract(contract, files):
    fields = {'schema_version','id','version','consumer','description','configuration','operations',
              'resources','estimates','errors','risk','limits','limitations','execution',
              'client','api','policy','prerequisites'}
    require(isinstance(contract,dict) and set(contract)==fields, 'Invalid Skill contract fields')
    identity = contract['id']
    require(isinstance(identity, str) and re.fullmatch(NAME, identity), 'Invalid Skill identity')
    require(type(contract.get('schema_version')) is int and contract['schema_version'] == 2
            and re.fullmatch(VERSION, contract.get('version', '')), 'Versioned Skill contract required')
    require(contract.get('consumer') == 'cloud-skill', 'Contract consumer must be cloud-skill')
    localized(contract.get('description'), identity)
    require(isinstance(contract.get('operations'), dict) and contract['operations'], 'Operations required')
    for name, operation in contract['operations'].items():
        schema(operation.get('input'), f'{identity}/{name}/input')
        schema(operation.get('output'), f'{identity}/{name}/output')
    schema(contract.get('configuration'), identity+'/configuration')
    require(isinstance(contract['resources'],dict) and set(contract['resources']) == {'memory_bytes', 'storage_bytes'}, 'Resource dimensions required')
    require(isinstance(contract['estimates'],dict) and set(contract['estimates']) == set(contract['resources']), 'Resource estimates required')
    for value in contract['estimates'].values():
        require(value is None or type(value) is int and value >= 0, 'Invalid resource estimate')
    require(isinstance(contract.get('errors'), dict)
            and {'unsupported','unknown','invalid_input','provider_failure'} <= contract['errors'].keys()
            and all(isinstance(v,str) and v for v in contract['errors'].values()), 'Error semantics required')
    require(contract.get('risk') and contract.get('limitations'), 'Risk and limitations required')
    require(isinstance(contract['limits'],dict) and contract['limits'].get('automatic_retry') is False, 'Automatic retries are forbidden')
    require(contract.get('execution') == {'execution':'agent-host','device_integration':'unknown'},
            'Host execution does not establish device integration')
    client = contract.get('client', {})
    require(isinstance(client,dict) and set(client)=={'python_minimum','operations'}, 'Invalid client binding fields')
    require({'SKILL.md','contract.json'} <= files.keys()
            and client.get('python_minimum'), 'Entrypoint, contract and Skill guidance must be pinned')
    require(set(client.get('operations', {})) == set(contract['operations']), 'CLI operation coverage mismatch')
    for name, mapping in client['operations'].items():
        require(isinstance(mapping,dict) and set(mapping)=={'entrypoint','command','arguments','options','fixed_arguments'}, 'Invalid CLI mapping')
        require(isinstance(mapping['entrypoint'],str) and mapping['entrypoint'] in files
                and mapping['entrypoint'].endswith('.py'), 'CLI entrypoint must be a pinned Python file')
        require(isinstance(mapping['command'],list) and all(isinstance(part,str)
                and re.fullmatch(NAME,part) for part in mapping['command']), 'Invalid CLI subcommand')
        require(isinstance(mapping['arguments'],dict) and isinstance(mapping['options'],dict), 'CLI mappings must be objects')
        require(set(mapping['arguments'])==set(contract['operations'][name]['input']['properties'])
                and set(mapping['options'])==set(contract['configuration']['properties']), 'CLI mapping/schema mismatch')
        require(isinstance(mapping['fixed_arguments'],list), 'Fixed arguments must be a list')
        flags = [*mapping['arguments'].values(),*mapping['options'].values(),*mapping['fixed_arguments']]
        require(all(isinstance(flag,str) and re.fullmatch(r'--[a-z][a-z-]*',flag) for flag in flags)
                and len(flags)==len(set(flags)), 'Invalid or duplicate CLI flags')
    api = contract.get('api', {})
    require(isinstance(api,dict), 'API binding must be an object')
    require(set(api)=={'version','authorization','routing','operations'}
            and isinstance(api['version'],str) and api['version']
            and api['authorization']=='Device' and api['routing']=='service-fixed', 'Public fixed-routing API identity required')
    require(isinstance(api['operations'],dict) and set(api['operations'])==set(contract['operations']), 'API operation coverage mismatch')
    for binding in api['operations'].values():
        require(isinstance(binding,dict) and set(binding)=={'method','path'}
                and binding['method'] in ('GET','POST') and isinstance(binding['path'],str)
                and binding['path'].startswith('/deviceapi/'), 'Invalid public API binding')
    pre = contract.get('prerequisites', {})
    require(isinstance(pre,dict), 'Prerequisites must be an object')
    require(all(type(pre.get(k)) is bool for k in ('network','tls','loopback_http')) and pre.get('privacy'),
            'Network/TLS/privacy prerequisites required')
    for key in ('secret_refs','environment_refs'):
        require(isinstance(pre.get(key),list)
                and all(isinstance(v,str) and re.fullmatch(r'[A-Z][A-Z0-9_]*',v) for v in pre[key]),
                'Only environment names may identify configuration or credentials')
    return policy(contract, files)


def load_package(root, skill):
    """Load one explicitly named package and verify its complete released bytes."""
    record = read_json(safe_path(root, record_path(skill)))
    require(isinstance(record,dict) and set(record)=={'schema_version','id','version','api_version','contract_version','policy_version','files','source'}
            and record['id']==skill and type(record['schema_version']) is int and record['schema_version']==1,
            'Invalid Skill release record')
    for key in ('version','contract_version','policy_version'):
        require(isinstance(record[key],str) and re.fullmatch(VERSION,record[key]), 'Invalid '+key)
    source = record['source']
    require(isinstance(source,dict) and source.get('repository') and re.fullmatch(r'[0-9a-f]{40}',source.get('commit',''))
            and type(source.get('dirty')) is bool, 'Original import provenance required')
    safe_path(root, source['import_manifest'])
    files = record['files']
    require(isinstance(files,dict) and files, 'Complete package inventory required')
    for path, checksum in files.items():
        safe_path(Path(root)/'skills'/skill, path)
        require(isinstance(checksum,str) and re.fullmatch(r'[0-9a-f]{64}',checksum), 'Invalid package fingerprint')
    require(package_inventory(Path(root)/'skills'/skill)==files,
            skill+': package differs from reviewed release; use the candidate workflow')
    contract = read_json(Path(root)/'skills'/skill/'contract.json')
    validate_contract(contract, files)
    require(contract['id']==skill and contract['version']==record['contract_version']
            and contract['api']['version']==record['api_version']
            and contract['policy']['version']==record['policy_version'], 'Independent contract/API/policy versions differ from release')
    return record, contract


def prerequisites(contract, environment=None, limits=None):
    """Check declared conditions for one Skill; never inspect credentials or hardware."""
    environment = {} if environment is None else environment
    limits = {} if limits is None else limits
    require(isinstance(environment,dict) and isinstance(limits,dict), 'Environment and limits must be objects')
    require(set(environment)<={'network','tls','loopback','secret_refs','environment_refs','privacy_approved'},
            'Unknown environment field; never supply credential values')
    for name in ('network','tls','loopback','privacy_approved'):
        require(name not in environment or type(environment[name]) is bool, 'Environment decisions must be booleans')
    for name in ('secret_refs','environment_refs'):
        require(name not in environment or isinstance(environment[name],list)
                and all(isinstance(v,str) and re.fullmatch(r'[A-Z][A-Z0-9_]*',v) for v in environment[name]),
                'Environment references must be names')
    require(set(limits)<=contract['resources'].keys()
            and all(type(v) is int and v>=0 for v in limits.values()), 'Invalid resource constraint')
    unknown, conflicts = [], []
    pre = contract['prerequisites']
    for key in ('network','tls'):
        if key=='tls' and pre['loopback_http'] and environment.get('loopback') is True:
            continue
        if pre[key] and environment.get(key) is False:
            conflicts.append(key+' is required')
        elif pre[key] and environment.get(key) is not True:
            unknown.append(key+' availability is unknown')
    if pre['privacy']!='no external data' and environment.get('privacy_approved') is not True:
        unknown.append('Data processing/privacy decision is required')
    for key in ('secret_refs','environment_refs'):
        if not set(pre[key])<=set(environment.get(key,[])):
            unknown.append('Required '+key+' are not configured')
    for key,maximum in limits.items():
        if contract['estimates'][key] is None:
            unknown.append(key+' bound is unknown')
        elif contract['estimates'][key]>maximum:
            conflicts.append(key+' exceeds the limit')
    return {'status':'unsupported' if conflicts else ('unknown' if unknown else 'eligible'),
            'unknowns':unknown,'conflicts':conflicts,'execution':'not_run','device_integration':'unknown'}


def selection(root, item):
    require(isinstance(item,dict) and set(item)=={'skill','configuration','environment','limits'},
            'Selection requires Skill, configuration, environment and limits')
    record, contract = load_package(root, item['skill'])
    effective = policy(contract, record['files'])
    require(isinstance(item['configuration'],dict), 'Configuration must be an object')
    configuration = {**contract['policy']['defaults'],**item['configuration']}
    payload(effective['configuration'],configuration,'configuration')
    state = prerequisites(contract, item['environment'], item['limits'])
    require(state['status']=='eligible', 'Skill prerequisites are unsupported or unknown: '+str(state))
    return {'skill':item['skill'],'version':record['version'],'configuration':item['configuration'],
            'effective_configuration':configuration,**state}


def selected_graph(root, items):
    require(isinstance(items,list), 'Skill selections must be a list')
    graph = SourceGraph(root)
    seen = set()
    for item in items:
        selected = selection(root,item)
        sid = selected['skill']
        require(sid not in seen, 'Duplicate Skill selection')
        seen.add(sid)
        graph.resolve(package_graph(root,sid).files)
    return graph


def package_graph(root, skill):
    record, _ = load_package(root,skill)
    graph = SourceGraph(root)
    graph.resolve([record_path(skill),record['source']['import_manifest'],'tools/skill_packages/upstream.json',
                   'tools/codecraft/skill_contracts.py','tools/codecraft/registry.py',
                   'tools/codecraft/graph.py','tools/codecraft/io_utils.py',
                   'docs/architecture/skill-contracts.md',
                   *['skills/'+skill+'/'+name for name in record['files']]])
    return graph


def check_packages(root, skills_root=None):
    import shutil
    import subprocess
    import sys
    import tempfile
    checks = []
    installed = Path(skills_root or Path(root)/'skills').expanduser().resolve()
    for sid in sorted(registrations(root)):
        record, contract = load_package(root,sid)
        package = safe_path(installed,sid,exists=False)
        actual = package_inventory(package) if package.is_dir() else {}
        drift = sorted(name for name in actual.keys() | record['files'].keys() if actual.get(name)!=record['files'].get(name))
        if drift:
            checks.append({'name':sid,'status':'failed','reason':'Skill differs from reviewed release','drift':drift})
            continue
        with tempfile.TemporaryDirectory(prefix='codecraft-skill-check-') as folder:
            verified = Path(folder)/sid
            for name,checksum in record['files'].items():
                out = verified/name
                out.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(safe_path(package,name),out)
                require(digest(out)==checksum,'Package changed while copying')
            valid = True
            for mapping in contract['client']['operations'].values():
                run = subprocess.run([sys.executable,'-E','-s','-B',str(verified/mapping['entrypoint']),*mapping['command'],'--help'],
                                     cwd=folder,capture_output=True,text=True,timeout=30)
                flags = [*mapping['arguments'].values(),*mapping['options'].values(),*mapping['fixed_arguments']]
                valid = valid and run.returncode==0 and all(flag in run.stdout for flag in flags)
        checks.append({'name':sid,'status':'passed' if valid else 'failed',
                       'reason':'Reviewed package and isolated CLI checked.' if valid else 'Skill CLI contract mismatch',
                       'source_digest':object_digest(record['files']),'api_execution':'not_run'})
    return checks

TYPES={'object':dict,'array':list,'string':str,'integer':int,'number':(int,float),'boolean':bool,'null':type(None)}


def finite_number(value):
    return type(value) is int or type(value) is float and math.isfinite(value)


def schema(spec, label):
    require(isinstance(spec,dict) and spec.get('type') in TYPES and spec.get('description'), f'{label}: typed, described schema required')
    if spec['type']=='object':
        require(isinstance(spec.get('properties'),dict) and type(spec.get('additionalProperties')) is bool, f'{label}: explicit object properties policy required')
        require(isinstance(spec.get('required'),list) and set(spec['required']) <= spec['properties'].keys(), f'{label}: invalid required properties')
        for key,child in spec['properties'].items():schema(child,label+'/'+key)
    elif spec['type']=='array':schema(spec.get('items'),label+'/items')
    if 'enum' in spec:require(isinstance(spec['enum'],list) and spec['enum'],f'{label}: empty enum')
    if 'minimum' in spec and 'maximum' in spec:require(spec['minimum']<=spec['maximum'],f'{label}: inverted range')
    if 'pattern' in spec:re.compile(spec['pattern'])
    if 'policy_default' in spec:require(type(spec['policy_default']) is bool,f'{label}: policy_default must be boolean')


def payload(spec, value, label='payload'):
    if value is None and spec.get('nullable'):
        return
    require(isinstance(value,TYPES[spec['type']]) and not (spec['type'] in ('integer','number') and type(value) is bool),f'{label}: type mismatch')
    if spec['type']=='object':
        require(set(spec['required'])<=value.keys(),f'{label}: missing required fields')
        require(spec['additionalProperties'] or set(value)<=spec['properties'].keys(),f'{label}: unknown fields')
        for key,item in value.items():
            if key in spec['properties']:payload(spec['properties'][key],item,label+'/'+key)
    elif spec['type']=='array':
        for i,item in enumerate(value):payload(spec['items'],item,f'{label}/{i}')
    if 'enum' in spec:require(value in spec['enum'],f'{label}: outside enum')
    if 'minimum' in spec:require(value>=spec['minimum'],f'{label}: below minimum')
    if 'maximum' in spec:require(value<=spec['maximum'],f'{label}: above maximum')
    if 'minLength' in spec:require(len(value)>=spec['minLength'],f'{label}: too short')
    if 'maxLength' in spec:require(len(value)<=spec['maxLength'],f'{label}: too long')
    if 'oneRequired' in spec:require(sum(key in value for key in spec['oneRequired'])==1,f'{label}: select exactly one input')
    if 'pattern' in spec:require(re.fullmatch(spec['pattern'],value),f'{label}: pattern mismatch')


def constrained_schema(base, constraints, label):
    """Apply a restrictive schema fragment without replacing operation semantics."""
    allowed={'properties','items','required','additionalProperties','enum',
             'minimum','maximum','minLength','maxLength','pattern'}
    require(isinstance(constraints,dict) and set(constraints)<=allowed,
            f'{label}: unknown Service policy schema constraint')
    effective=copy.deepcopy(base)
    if 'properties' in constraints:
        properties=constraints['properties']
        require(base['type']=='object' and isinstance(properties,dict) and set(properties)<=base['properties'].keys(),
                f'{label}: Service policy cannot add or replace contract fields')
        for key,value in properties.items():
            effective['properties'][key]=constrained_schema(base['properties'][key],value,label+'/'+key)
    if 'items' in constraints:
        require(base['type']=='array',f'{label}: items requires array')
        effective['items']=constrained_schema(base['items'],constraints['items'],label+'/items')
    if 'required' in constraints:
        required=constraints['required']
        require(base['type']=='object' and isinstance(required,list) and all(isinstance(x,str) for x in required)
                and set(required)<=base['properties'].keys(),f'{label}: invalid required fields')
        effective['required']=sorted(set(base['required'])|set(required))
    if 'additionalProperties' in constraints:
        require(base['type']=='object' and constraints['additionalProperties'] is False,
                f'{label}: Service policy may only prohibit additional properties')
        effective['additionalProperties']=False
    for key in ('minimum','maximum','minLength','maxLength'):
        if key not in constraints:continue
        value=constraints[key]
        if key.endswith('Length'):
            require(base['type']=='string' and type(value) is int and value>=0,f'{label}: invalid length constraint')
        else:
            require(base['type'] in ('integer','number') and finite_number(value),
                    f'{label}: invalid numeric constraint')
        if key in base:
            require(value>=base[key] if key.startswith('min') else value<=base[key],
                    f'{label}: Service policy cannot weaken {key}')
        effective[key]=value
    if 'pattern' in constraints:
        pattern=constraints['pattern']
        require(base['type']=='string' and isinstance(pattern,str),f'{label}: invalid pattern')
        require('pattern' not in base or pattern==base['pattern'],f'{label}: Service policy cannot replace contract pattern')
        try:re.compile(pattern)
        except re.error:require(False,f'{label}: invalid pattern')
        effective['pattern']=pattern
    if 'enum' in constraints:
        values=constraints['enum']
        require(isinstance(values,list) and values,f'{label}: empty Service policy enum')
        for value in values:payload(base,value,label+'/enum')
        effective['enum']=copy.deepcopy(values)
    schema(effective,label)
    if 'minLength' in effective and 'maxLength' in effective:
        require(effective['minLength']<=effective['maxLength'],f'{label}: inverted length range')
    for value in effective.get('enum',[]):payload(effective,value,label+'/enum')
    return effective


def _limit_facts(value, label):
    """Validate declared service facts; selected Skill owns byte/protocol checks."""
    if value is None or type(value) is bool:return
    if type(value) in (int,float):
        require(finite_number(value) and value>=0,f'{label}: invalid service limit')
    elif isinstance(value,str):require(bool(value),f'{label}: empty service limit')
    elif isinstance(value,list):
        require(bool(value),f'{label}: empty service limit')
        for item in value:_limit_facts(item,label)
    else:
        require(isinstance(value,dict) and value and all(isinstance(k,str) and k for k in value),f'{label}: invalid service limits')
        for key,item in value.items():_limit_facts(item,label+'/'+key)


def policy(contract, files):
    """Return validated effective schemas; no files, credentials or API are read."""
    identity=contract['id'];value=contract.get('policy')
    keys={'schema_version','version','defaults','limits','configuration','operations','billing','sources'}
    require(isinstance(value,dict) and set(value)==keys and type(value['schema_version']) is int and value['schema_version']==1,
            f'{identity}: versioned Service policy policy required')
    require(isinstance(value['version'],str) and re.fullmatch(r'\d+\.\d+\.\d+',value['version']),f'{identity}: invalid policy version')
    require(isinstance(value['limits'],dict) and not set(value['limits']) & set(contract['limits']),
            f'{identity}: Service policy limits cannot override Skill semantic contract semantics')
    if value['limits']:_limit_facts(value['limits'],identity+'/policy/limits')
    sources=value['sources']
    require(isinstance(sources,list) and sources and all(isinstance(x,str) for x in sources)
            and set(sources)<=files.keys(),f'{identity}: policy sources must be pinned Skill files')
    billing=value['billing']
    require(isinstance(billing,dict) and set(billing)=={'status','unit','basis','amount'}
            and billing['status'] in ('declared','unknown'),f'{identity}: invalid billing policy')
    if billing['status']=='unknown':
        require(all(billing[key] is None for key in ('unit','basis','amount')),f'{identity}: unknown billing must remain unknown')
    else:
        require(all(isinstance(billing[key],str) and billing[key] for key in ('unit','basis')),
                f'{identity}: billing unit and basis required')
        amount=billing['amount']
        require(amount is None or finite_number(amount) and amount>=0,
                f'{identity}: invalid billing amount')
    config=constrained_schema(contract['configuration'],value['configuration'],identity+'/configuration')
    defaults=value['defaults']
    require(isinstance(defaults,dict) and set(defaults)<=config['properties'].keys(),f'{identity}: invalid Service policy defaults')
    for name,default in defaults.items():
        require(contract['configuration']['properties'][name].get('policy_default') is True,
                f'{identity}: {name} requires explicit configuration; no Service policy default')
        payload(config['properties'][name],default,identity+'/defaults/'+name)
    operations=value['operations']
    require(isinstance(operations,dict) and set(operations)==set(contract['operations']),f'{identity}: policy operation coverage mismatch')
    effective={}
    for name,operation in contract['operations'].items():
        overrides=operations[name]
        require(isinstance(overrides,dict) and set(overrides)=={'input','output'},f'{identity}: input/output policy constraints required')
        effective[name]={kind:constrained_schema(operation[kind],overrides[kind],identity+'/'+name+'/'+kind)
                         for kind in ('input','output')}
    return {'configuration':config,'operations':effective}


def package_inventory(package):
    """Fingerprint a standalone package, not a native build source directory."""
    package=Path(package)
    require(package.is_dir() and not package.is_symlink(), 'Skill package must be a real directory')
    files={}
    for path in sorted(package.rglob('*')):
        relative=path.relative_to(package)
        if '__pycache__' in relative.parts or path.name=='.DS_Store':
            continue
        require(not path.is_symlink(), f'Skill package must not contain symlinks: {relative}')
        if path.is_file():
            require(path.name!='.env' and not (path.name.startswith('.env.') and path.name!='.env.example') and not {'secrets','.secrets'} & set(relative.parts),f'Private file inside Skill package: {relative}')
            files[relative.as_posix()]=digest(path)
    return files
