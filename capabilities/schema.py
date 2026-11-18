"""Cloud Skill contracts, Provider registrations and attributable model artifacts."""
import copy
import math
import re

from pathlib import Path

from io_utils import digest, localized, require, safe_path

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
    if 'provider_default' in spec:require(type(spec['provider_default']) is bool,f'{label}: provider_default must be boolean')


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


def validate(root, capability):
    identity=capability['id']
    require(capability.get('schema_version')==2 and re.fullmatch(r'\d+\.\d+\.\d+',capability.get('version','')),f'{identity}: versioned Capability required')
    require(capability.get('consumer')=='cloud-skill',f'{identity}: consumer must be cloud-skill')
    localized(capability.get('description'),identity)
    require(capability.get('operations') and isinstance(capability['operations'],dict),f'{identity}: operations required')
    for name,operation in capability['operations'].items():
        schema(operation.get('input'),f'{identity}/{name}/input')
        schema(operation.get('output'),f'{identity}/{name}/output')
    schema(capability.get('configuration'),identity+'/configuration')
    require(isinstance(capability.get('resources'),dict) and set(capability['resources'])=={'memory_bytes','storage_bytes'},f'{identity}: resource dimensions required')
    require(isinstance(capability.get('errors'),dict) and {'unsupported','unknown','invalid_input','provider_failure'}<=capability['errors'].keys(),f'{identity}: error contract required')
    require(all(isinstance(text,str) and text for text in capability['errors'].values()),f'{identity}: empty error semantics')
    require(capability.get('risk') and capability.get('limitations'),f'{identity}: risk and limitations required')
    require(isinstance(capability.get('limits'),dict) and capability['limits'].get('automatic_retry') is False,
            f'{identity}: explicit no-automatic-retry contract required')
    safe_path(root,capability['agent_route'])


def constrained_schema(base, constraints, label):
    """Apply a restrictive schema fragment without replacing operation semantics."""
    allowed={'properties','items','required','additionalProperties','enum',
             'minimum','maximum','minLength','maxLength','pattern'}
    require(isinstance(constraints,dict) and set(constraints)<=allowed,
            f'{label}: unknown Provider schema constraint')
    effective=copy.deepcopy(base)
    if 'properties' in constraints:
        properties=constraints['properties']
        require(base['type']=='object' and isinstance(properties,dict) and set(properties)<=base['properties'].keys(),
                f'{label}: Provider cannot add or replace contract fields')
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
                f'{label}: Provider may only prohibit additional properties')
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
                    f'{label}: Provider cannot weaken {key}')
        effective[key]=value
    if 'pattern' in constraints:
        pattern=constraints['pattern']
        require(base['type']=='string' and isinstance(pattern,str),f'{label}: invalid pattern')
        require('pattern' not in base or pattern==base['pattern'],f'{label}: Provider cannot replace contract pattern')
        try:re.compile(pattern)
        except re.error:require(False,f'{label}: invalid pattern')
        effective['pattern']=pattern
    if 'enum' in constraints:
        values=constraints['enum']
        require(isinstance(values,list) and values,f'{label}: empty Provider enum')
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


def policy(entry, capability):
    """Return validated effective schemas; no files, credentials or API are read."""
    identity=entry['id'];value=entry.get('policy')
    keys={'schema_version','version','defaults','limits','configuration','operations','billing','sources'}
    require(isinstance(value,dict) and set(value)==keys and type(value['schema_version']) is int and value['schema_version']==1,
            f'{identity}: versioned Provider policy required')
    require(isinstance(value['version'],str) and re.fullmatch(r'\d+\.\d+\.\d+',value['version']),f'{identity}: invalid policy version')
    require(isinstance(value['limits'],dict) and not set(value['limits']) & set(capability['limits']),
            f'{identity}: Provider limits cannot override Capability semantics')
    if value['limits']:_limit_facts(value['limits'],identity+'/policy/limits')
    sources=value['sources']
    require(isinstance(sources,list) and sources and all(isinstance(x,str) for x in sources)
            and set(sources)<=entry['skill']['files'].keys(),f'{identity}: policy sources must be pinned Skill files')
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
    config=constrained_schema(capability['configuration'],value['configuration'],identity+'/configuration')
    defaults=value['defaults']
    require(isinstance(defaults,dict) and set(defaults)<=config['properties'].keys(),f'{identity}: invalid Provider defaults')
    for name,default in defaults.items():
        require(capability['configuration']['properties'][name].get('provider_default') is True,
                f'{identity}: {name} requires explicit configuration; no Provider default')
        payload(config['properties'][name],default,identity+'/defaults/'+name)
    operations=value['operations']
    require(isinstance(operations,dict) and set(operations)==set(capability['operations']),f'{identity}: policy operation coverage mismatch')
    effective={}
    for name,operation in capability['operations'].items():
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


def provider(root, entry, capability):
    identity=entry['id']
    require(entry.get('schema_version')==2 and identity.count('/')==1 and identity.startswith(capability['id']+'/'),f'{identity}: invalid Provider identity/schema')
    require(entry.get('capability')==capability['id'] and entry.get('contract_version')==capability['version'],f'{identity}: Provider contract version mismatch')
    require(entry.get('kind') in ('repository-skill','external-skill'),f'{identity}: unsupported Skill Provider kind')
    skill=entry.get('skill',{})
    require(isinstance(skill,dict) and skill.get('id') and skill.get('version') and skill.get('api_version') and skill.get('entrypoint') and isinstance(skill.get('files'),dict) and skill['files'],f'{identity}: pinned Skill required')
    require(re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',skill['id']),f'{identity}: invalid Skill name')
    require(skill['entrypoint'] in skill['files'] and 'SKILL.md' in skill['files'],f'{identity}: entrypoint/Skill document must be fingerprinted')
    for path,checksum in skill['files'].items():
        require(not path.startswith('/') and '..' not in path.split('/') and re.fullmatch(r'[0-9a-f]{64}',checksum),f'{identity}: invalid external source fingerprint')
    require(entry.get('source',{}).get('repository') and re.fullmatch(r'[0-9a-f]{40}',entry['source'].get('commit','')) and type(entry['source'].get('dirty')) is bool,f'{identity}: external source provenance required')
    require(entry.get('target_policy')=={'execution':'agent-host','device_integration':'unknown'},f'{identity}: host Skill execution is not device firmware support')
    require(set(entry.get('operations',{}))==set(capability['operations']),f'{identity}: operation coverage mismatch')
    for name,operation in entry['operations'].items():
        require(isinstance(operation,dict) and isinstance(operation.get('arguments'),dict) and isinstance(operation.get('options'),dict),f'{identity}: CLI mappings must be objects')
        require(set(operation.get('arguments',{}))==set(capability['operations'][name]['input']['properties']),f'{identity}: CLI argument/input mismatch')
        require(set(operation.get('options',{}))==set(capability['configuration']['properties']),f'{identity}: CLI option/configuration mismatch')
        fixed=operation.get('fixed_arguments',[])
        require(isinstance(fixed,list),f'{identity}: fixed arguments must be a list')
        flags=[*operation['arguments'].values(),*operation['options'].values(),*fixed]
        require(all(isinstance(flag,str) and re.fullmatch(r'--[a-z][a-z-]*',flag) for flag in flags),f'{identity}: invalid CLI flag')
        require(len(flags)==len(set(flags)),f'{identity}: ambiguous duplicate CLI flag')
    require(set(entry.get('resources',{}))==set(capability['resources']),f'{identity}: resource dimensions required')
    for bound in entry['resources'].values():require(bound is None or type(bound) is int and bound>=0,f'{identity}: invalid resource bound')
    pre=entry.get('prerequisites',{})
    require(isinstance(pre,dict) and type(pre.get('network')) is bool and type(pre.get('tls')) is bool and pre.get('privacy'),f'{identity}: network/TLS/privacy prerequisites required')
    require(type(pre.get('loopback_http')) is bool,f'{identity}: loopback HTTP policy must be explicit')
    require(isinstance(pre.get('secret_refs'),list) and isinstance(pre.get('environment_refs'),list),f'{identity}: credential/environment references required')
    require(all(re.fullmatch(r'[A-Z][A-Z0-9_]*',name) for name in pre['secret_refs']+pre['environment_refs']),f'{identity}: only environment names may identify credentials')
    require(entry.get('limitations') and isinstance(entry.get('models'),list) and isinstance(entry.get('dependencies'),list),f'{identity}: models/dependencies/limitations required')
    policy(entry,capability)
    for path in entry['dependencies']:safe_path(root,path)
    if entry['kind']=='repository-skill':
        require(skill.get('path')=='skills/'+skill['id'],f'{identity}: repository Skill path mismatch')
        package=safe_path(root,skill['path'])
        require(package.is_dir() and skill['path'] in entry['dependencies'],f'{identity}: repository Skill must be a declared dependency')
        actual=package_inventory(package)
        require(actual==skill['files'],f'{identity}: repository Skill differs from pinned source; review package changes and update its Provider')


def model(root, artifact):
    require(artifact.get('schema_version')==2 and all(artifact.get(key) for key in ('id','task','version','runtime','quantization','source','license','sha256','path')), 'Incomplete Model Artifact')
    require(artifact['license']!='unknown' and digest(safe_path(root,artifact['path']))==artifact['sha256'],'Model license/checksum mismatch')
    require(all(type(artifact.get(key)) is int and artifact[key]>=0 for key in ('memory_bytes','storage_bytes')),'Model resource requirements missing')
