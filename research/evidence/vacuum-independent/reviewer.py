"""Astra's independent numerical review, not a registered store checker."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import sys
import time

import numpy as np

SOURCE_SHA = 'f948c9be21949f84e1679ab380dde6553183782bdc46f4be8c7a8845da732a68'
FROZEN_DECISION_SHA = 'c730771bdfd12f7ec2f48c6f5d20475b105c0b2927fb800a3cfc503ff7ceb3c9'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('Refusing to replace original review output')
    raw = args.source.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA:
        raise ValueError('Original switching source hash mismatch')
    started = time.perf_counter()
    spec = importlib.util.spec_from_file_location('reviewed_original_switching', args.source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    chi = module.ChiFn(0.0, 1.0)
    inner_rules = {}
    for order in (256, 512):
        nodes, weights = np.polynomial.legendre.leggauss(order)
        inner_rules[order] = (nodes, weights * chi(nodes))

    def direct_transform(q, order):
        nodes, weighted_chi = inner_rules[order]
        # Symmetry removes the imaginary odd integral; no candidate transform is used.
        q = np.asarray(q, dtype=float).reshape(-1)
        return np.sum(np.cos(q[:, None] * nodes) * weighted_chi, axis=1)

    def response(a, outer_order, inner_order):
        nodes, weights = np.polynomial.legendre.leggauss(outer_order)
        # These integral limits are integers for the frozen five cases.
        edges = np.arange(a, 65.0, 1.0)
        q = ((edges[:-1, None] + edges[1:, None]) / 2 + nodes / 2).reshape(-1)
        all_weights = np.tile(weights / 2, len(edges) - 1)
        values = direct_transform(q, inner_order)
        return float(np.sum(all_weights * (q - a) * values**2) / (4 * np.pi**2))

    rows = []
    for a in (-4.0, -1.0, 0.0, 1.0, 4.0):
        first = response(a, 16, 256)
        inner_refined = response(a, 16, 512)
        final = response(a, 32, 512)
        tolerance = 1e-8 + 1e-6 * abs(final)
        tail = 64 * np.pi**6 / (75 * 64**8)
        row = dict(a=a, outer16_inner256=first, outer16_inner512=inner_refined,
                   outer32_inner512=final, inner_change=abs(first-inner_refined),
                   outer_change=abs(inner_refined-final), tolerance=tolerance,
                   analytic_tail_bound=float(tail))
        row['review_refinement_pass'] = bool(final >= 0 and np.isfinite(final)
            and row['inner_change'] <= tolerance/4
            and row['outer_change'] <= tolerance/4 and tail <= tolerance/4)
        rows.append(row)
    poles = np.array([-2*np.pi, -np.pi, 0.0, np.pi, 2*np.pi])
    sample_q = np.unique(np.concatenate([poles, poles-1e-8, poles+1e-8,
                                        [0.37, 1.73, 7.1, 13.2]]))
    special = direct_transform(poles, 512)
    expected_special = np.array([1/8, 1/2, 3/4, 1/2, 1/8])
    values = {row['a']: row for row in rows}
    differences = []
    for a in (1.0, 4.0):
        measured = values[-a]['outer32_inner512'] - values[a]['outer32_inner512']
        expected = 35*a/(128*np.pi)
        allowed = values[-a]['tolerance'] + values[a]['tolerance']
        differences.append(dict(a=a, measured=measured, expected=float(expected),
                                discrepancy=abs(measured-expected), tolerance=allowed,
                                passed=bool(abs(measured-expected) <= allowed)))
    result = dict(reviewer='Astra independent numerical review; local model label',
        source_sha256=SOURCE_SHA, frozen_decision_sha256=FROZEN_DECISION_SHA,
        checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        environment=dict(python=sys.version.split()[0], numpy=np.__version__, platform=platform.platform()),
        method='Original ChiFn at Gauss-Legendre time nodes; direct cosine Fourier integral; separate composite Gauss-Legendre frequency integral',
        conventions='hbar=c=1; delta=1; center=0; a=E*delta; positive E excitation; dimensionless response, not probability',
        Q=64, invocation_cap_seconds=60, rows=rows,
        transform_samples=[dict(q=float(q), direct_g=float(g)) for q, g in zip(sample_q, direct_transform(sample_q,512))],
        special_point_max_error=float(np.max(np.abs(special-expected_special))),
        response_differences=differences,
        numerical_elapsed_seconds=time.perf_counter()-started,
        limits=['Empirical quadrature refinement, not a rigorous quadrature error certificate.',
                'Analytic tail bound assumes the independently derived transform identity.',
                'No candidate code/result imported. No domain certification or product-value claim.'])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps({'rows':rows,'numerical_elapsed_seconds':result['numerical_elapsed_seconds']}))


if __name__ == '__main__':
    main()
