"""Trusted bounded graph-fixture checker. Reads JSON only; never imports a candidate."""
import json
import sys


def check(criterion, candidate):
    n, degree = criterion['n'], criterion['degree']
    if not isinstance(candidate, dict) or set(candidate) != {'edges'}:
        return False, 'Expected only an edges array, not code or acceptance settings.'
    edges = candidate['edges']
    if not isinstance(edges, list) or len(edges) > n * (n - 1) // 2:
        return False, 'Invalid edge count.'
    adjacency = [set() for _ in range(n)]
    for edge in edges:
        if not isinstance(edge, list) or len(edge) != 2 or any(type(x) is not int for x in edge):
            return False, 'Edges require two integer vertices.'
        a, b = edge
        if not (0 <= a < n and 0 <= b < n) or a == b or b in adjacency[a]:
            return False, 'Out-of-range vertex, self-edge, or duplicate edge.'
        adjacency[a].add(b); adjacency[b].add(a)
    if any(len(neighbors) != degree for neighbors in adjacency):
        return False, 'Degree constraint failed for this candidate; no impossibility conclusion.'
    if criterion['triangle_free'] and any(adjacency[a] & adjacency[b] for a, b in edges):
        return False, 'Triangle found in this candidate; no impossibility conclusion.'
    return True, 'Exact finite graph constraints passed. This is a mechanics fixture, not research value.'


if __name__ == '__main__':
    request = json.loads(sys.stdin.buffer.read(1_000_001))
    valid, detail = check(request['criterion'], request['candidate'])
    print(json.dumps({'valid': valid, 'detail': detail}))
