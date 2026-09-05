"""Deterministic test worker. Fresh process, no model, no research-value inference."""
import hashlib
import json
from pathlib import Path
import sys
import time


def run(package):
    start = time.perf_counter()
    package = Path(package)
    manifest = json.loads((package / 'manifest.json').read_text(encoding='utf-8'))
    for name, expected in manifest.items():
        path = (package / name).resolve()
        if not path.is_relative_to(package.resolve()):
            raise ValueError('unsafe package manifest')
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('package changed')
    target = json.loads((package / 'target.json').read_text(encoding='utf-8'))
    assignment = json.loads((package / 'assignment.json').read_text(encoding='utf-8'))
    # Inspect every available condition input. No global memory or previous-process state.
    read_files = [name for name in manifest if name != 'target.json']
    for name in read_files:
        (package / name).read_bytes()
    n = target['acceptance']['criterion']['n']
    candidate = {'edges': [[i, (i + 1) % n] for i in range(n)]}
    print(json.dumps({'candidate': candidate, 'assignment': assignment,
                      'observed_files': sorted(manifest),
                      'elapsed_seconds': time.perf_counter() - start,
                      'worker': 'deterministic cycle constructor; NOT a model',
                      'limitation': 'Exercises package mechanics only; ignores representation for solving.'}))


if __name__ == '__main__':
    run(sys.argv[1])
