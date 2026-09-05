#!/usr/bin/env python3
"""Validate map structure and citation integrity, not scientific truth."""
import json
import re
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
KINDS = {'observation', 'model', 'mechanism', 'principle', 'open-question'}
RELATIONS = {'supports', 'explains', 'leaves-open', 'challenges', 'alternative-to', 'informs'}

class Fail(ValueError):
    pass

def require(condition, message):
    if not condition:
        raise Fail(message)

def text(value, context):
    require(isinstance(value, str) and bool(value.strip()), f'{context}: needs nonempty text')

def records(items, context):
    require(isinstance(items, list) and bool(items), f'{context}: needs a nonempty list')
    result = {}
    for item in items:
        require(isinstance(item, dict), f'{context}: expected an object')
        id = item.get('id')
        require(isinstance(id, str) and re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', id), f'{context}: invalid id')
        require(id not in result, f'{context}: duplicate id {id}')
        result[id] = item
    return result

def refs(values, sources, context):
    require(isinstance(values, list) and bool(values), f'{context}: needs sources')
    require(all(isinstance(v, str) and v in sources for v in values), f'{context}: unknown source')
    require(len(values) == len(set(values)), f'{context}: duplicate source')

def check(g):
    require(isinstance(g, dict), 'map must be an object')
    require(g.get('version') == 3, 'expected schema version 3')
    require(set(g.get('kinds', {})) == KINDS, 'unknown or missing kinds')
    require(set(g.get('edge_types', {})) == RELATIONS, 'unknown or missing relations')
    for key in ('reviewed', 'editorial_note'):
        text(g.get(key), key)
    sources = records(g.get('sources'), 'sources')
    nodes = records(g.get('nodes'), 'nodes')
    paths = records(g.get('paths'), 'paths')
    for id, s in sources.items():
        for key in ('author', 'title', 'url', 'type', 'scope'):
            text(s.get(key), f'source {id} {key}')
        url = urlparse(s['url'])
        require(url.scheme == 'https' and bool(url.netloc) and not url.username and not url.password, f'source {id}: unsafe URL')
        require(s['type'] in {'research', 'review', 'institution'}, f'source {id}: unknown type')
    for id, n in nodes.items():
        require(n.get('kind') in KINDS, f'node {id}: unknown kind')
        for key in ('domain', 'label', 'claim', 'scope', 'limits', 'question'):
            text(n.get(key), f'node {id} {key}')
        citations = n.get('sources')
        require(isinstance(citations, list) and bool(citations), f'node {id}: needs sources')
        for ref in citations:
            require(isinstance(ref, dict), f'node {id}: citation must be an object')
            text(ref.get('supports'), f'node {id} citation scope')
        refs([ref.get('id') for ref in citations], sources, f'node {id}')
        if n['kind'] == 'model':
            assumptions = n.get('assumptions')
            require(isinstance(assumptions, list) and bool(assumptions), f'model {id}: needs assumptions')
            for a in assumptions:
                text(a, f'model {id} assumption')
    edges = g.get('edges')
    require(isinstance(edges, list) and bool(edges), 'needs edges')
    seen, connected = set(), set()
    for e in edges:
        require(isinstance(e, dict), 'edge must be an object')
        a, b, kind = e.get('src'), e.get('dst'), e.get('type')
        require(isinstance(a, str) and isinstance(b, str) and a in nodes and b in nodes, 'dangling edge')
        require(a != b, 'self edge')
        require(isinstance(kind, str) and kind in RELATIONS, 'unknown edge relation')
        key = (a, kind, b)
        require(key not in seen, 'duplicate edge')
        seen.add(key); connected.update((a, b))
        text(e.get('explanation'), f'edge {key} explanation')
        refs(e.get('sources'), sources, f'edge {key}')
        if kind == 'leaves-open':
            require(nodes[b]['kind'] == 'open-question' and nodes[a]['kind'] != 'open-question', 'leaves-open must point from an explanation to an open question')
        if kind in {'supports', 'challenges'}:
            require(nodes[a]['kind'] == 'observation' and nodes[b]['kind'] in {'model','mechanism','principle'}, 'evidence relation needs an observation and an explanation')
        if kind == 'alternative-to':
            require(nodes[a]['kind'] == nodes[b]['kind'] == 'model', 'alternatives must be models')
    require(connected == set(nodes), 'unconnected node')
    covered = set()
    for id, p in paths.items():
        for key in ('title', 'subtitle', 'intro', 'takeaway'):
            text(p.get(key), f'path {id} {key}')
        ids = p.get('nodes')
        require(isinstance(ids, list) and bool(ids), f'path {id}: empty path')
        require(all(isinstance(i, str) and i in nodes for i in ids), f'path {id}: unknown node')
        require(len(set(ids)) == len(ids), f'path {id}: duplicate node')
        reached = {ids[0]}
        while True:
            expanded = reached | {e['dst'] for e in edges if e['src'] in reached and e['dst'] in ids} | {e['src'] for e in edges if e['dst'] in reached and e['src'] in ids}
            if reached == expanded:
                break
            reached = expanded
        require(reached == set(ids), f'path {id}: disconnected reading path')
        covered.update(ids)
    require(covered == set(nodes), 'nodes missing from reading paths')

def main():
    try:
        g = json.loads((ROOT / 'graph.json').read_text(encoding='utf-8'))
        check(g)
    except (Fail, json.JSONDecodeError) as error:
        print('FAIL:', error)
        return 1
    print(f"OK: {len(g['nodes'])} ideas, {len(g['edges'])} connections, {len(g['paths'])} paths, {len(g['sources'])} sources")
    print('Structure and references checked. Scientific accuracy requires editorial review.')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
