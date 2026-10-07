"""Split reviewed composite output into stable, generated project artifacts."""
import json
import re
from .store import GateError


def entries(content):
    blocks = re.findall(r'```asdlc-artifacts\s*\n(.*?)\n```', content, re.S)
    if not blocks:
        return []
    if len(blocks) != 1:
        raise GateError('One artifact inventory permitted per stage output')
    value = json.loads(blocks[0])
    if not isinstance(value, list) or len(value) > 500:
        raise GateError('Artifact inventory must be a bounded list')
    ids = set()
    for item in value:
        if not isinstance(item, dict) or set(item) != {'id', 'type', 'parent', 'content'}:
            raise GateError('Invalid individual artifact fields')
        if not isinstance(item['id'], str) or not re.fullmatch(r'[A-Z][A-Z0-9-]{0,63}', item['id']) or item['id'] in ids:
            raise GateError('Distinct portable artifact IDs required')
        ids.add(item['id'])
        if item['type'] not in ('initiative', 'epic', 'story') or not isinstance(item['content'], str) or not item['content'].strip():
            raise GateError('Artifact type/content required')
        if item['parent'] is not None and not isinstance(item['parent'], str):
            raise GateError('Artifact parent must be ID or null')
    return value


def validate_inventory(state, content):
    values = entries(content)
    if not values:
        return
    allowed = {'business-requirements': ('initiative', 'epic'), 'sprint-planning': ('story',)}
    if state['stage'] not in allowed or any(v['type'] not in allowed[state['stage']] for v in values):
        raise GateError('Individual artifact belongs to another stage')
    upstream = [v for ref in state['inputs'].get('upstream', []) for v in entries(ref['artifact']['content'])]
    upstream_ids = {v['id'] for v in upstream}
    if any(v['id'] in upstream_ids for v in values):
        raise GateError('Artifact ID already belongs to an upstream artifact')
    known = {v['id']: v['type'] for v in upstream + values}
    for item in values:
        expected = {'initiative': None, 'epic': 'initiative', 'story': 'epic'}[item['type']]
        if expected is None:
            if item['parent'] is not None:
                raise GateError('Initiative parent must be null')
        elif known.get(item['parent']) != expected:
            raise GateError('Artifact requires a traceable parent of the correct type')


def relative(item):
    folder = 'backlog/stories' if item['type'] == 'story' else 'requirements/' + item['type'] + 's'
    return folder + '/' + item['id'].lower() + '.md'
