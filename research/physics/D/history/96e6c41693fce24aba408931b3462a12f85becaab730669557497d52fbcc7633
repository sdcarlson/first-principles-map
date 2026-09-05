"""Reproduce only a switching-function prerequisite using pinned published code.

No Hawking spectrum, full paper reproduction, novel physics, or FPM effect estimate.
The numerical implementation comes from Shallue's BSD-3-Clause hawkrad/switching.py.
Analytic checks below use independent elementary trigonometric integrals.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import sys
import time

import numpy as np


def run(source, expected_sha256):
    source = Path(source).resolve()
    raw = source.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError('upstream source pin mismatch')
    # Execute only an explicitly supplied, inspected and pinned upstream source file.
    spec = importlib.util.spec_from_file_location('published_switching', source)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    rows = []
    start = time.perf_counter()
    for center in (0.0, 1.25):
        for delta in (0.125, 1.0, 4.0):
            chi = module.ChiFn(center, delta)
            for panels in (512, 1024):
                t = np.linspace(center-delta, center+delta, panels+1)
                values = chi(t)
                # Composite trapezoidal quadrature: independent from the exact integral.
                integral = float(np.sum((values[:-1]+values[1:])/2) * (2*delta/panels))
                squared = values**2
                integral_sq = float(np.sum((squared[:-1]+squared[1:])/2) * (2*delta/panels))
                # cos^4 integrates to 3 delta/4; cos^8 to 35 delta/64 over its support.
                errors = [abs(integral-3*delta/4), abs(integral_sq-35*delta/64)]
                support = bool(np.all(chi(np.array([center-2*delta, center+2*delta])) == 0))
                peak = abs(float(chi(center))-1.0)
                rows.append({'tau_mid': center, 'delta': delta, 'panels': panels,
                             'integral_chi': integral, 'integral_chi_squared': integral_sq,
                             'integral_errors': errors, 'support_pass': support,
                             'peak_error': peak,
                             'passed': support and peak <= 1e-12 and max(errors) <= 1e-10})
    return {'kind': 'published-code prerequisite reproduction, not a synthetic research history',
            'source': 'https://github.com/cshallue/hawking-radiation/blob/main/hawkrad/switching.py',
            'source_sha256': expected_sha256,
            'paper': 'https://arxiv.org/html/2501.06609v2#S2.SS2',
            'criterion_frozen_in_code': 'support=0 outside; peak=1 to 1e-12; integral errors <=1e-10 at both grids',
            'environment': {'python': platform.python_version(), 'numpy': np.__version__, 'platform': platform.platform()},
            'rows': rows, 'all_passed': all(x['passed'] for x in rows),
            'elapsed_seconds': time.perf_counter()-start,
            'scope_limit': 'Only switching-function support, peak and two normalization integrals tested. No curved-spacetime response, temperature, experimental observation, demand, or FPM benefit established.',
            'independence': 'Analytic identities differ from numerical quadrature; same local author reviewed both. No external domain review.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('expected_sha256')
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    if args.output.exists(): parser.error('output must be new')
    result = run(args.source, args.expected_sha256)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: result[k] for k in ('all_passed', 'scope_limit', 'elapsed_seconds')}, indent=2))
    sys.exit(0 if result['all_passed'] else 1)
