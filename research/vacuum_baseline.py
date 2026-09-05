"""Inertial Minkowski vacuum detector-response baseline.

Candidate implementation of the frozen flat-spacetime contract only.
No horizon, temperature, mode sum, new physics, or FPM-advantage claim.
"""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import platform
import sys
import time

import numpy as np


CANDIDATE = Path(__file__).resolve()
POLES = (0.0, math.pi, -math.pi, 2 * math.pi, -2 * math.pi)
POLE_G = {0.0: 0.75, math.pi: 0.5, -math.pi: 0.5,
          2 * math.pi: 0.125, -2 * math.pi: 0.125}
TRANSFORM_Q = POLES + (0.37, 1.73, 7.1, 13.2)
A_VALUES = (-4.0, -1.0, 0.0, 1.0, 4.0)
H_MAX = (1.0 / 16.0, 1.0 / 32.0, 1.0 / 64.0)
Q_FINE = 64.0
Q_DOUBLE = 128.0
DELTAS = (0.125, 1.0, 4.0)
CENTERS = (0.0, 1.25)


def _finite(*values):
    for value in values:
        arr = np.asarray(value)
        if arr.size == 0 or not np.all(np.isfinite(arr)):
            raise ValueError('nonfinite input')


def even_panel_count(length, h_max):
    _finite(length, h_max)
    if not (h_max > 0) or not (length > 0):
        raise ValueError('nonpositive interval or step')
    n = int(math.ceil(length / h_max))
    if n % 2:
        n += 1
    return max(n, 2)


def composite_simpson(y, h):
    y = np.asarray(y)
    n = y.size - 1
    if n < 2 or n % 2:
        raise ValueError('Simpson requires an even panel count')
    _finite(h)
    return (h / 3.0) * (y[0] + y[-1] + 4.0 * y[1::2].sum() + 2.0 * y[2:-1:2].sum())


def g(q):
    arr = np.asarray(q, dtype=np.float64)
    _finite(arr)
    x = arr / math.pi
    # Stable sinc expansion of the compact cos^4 transform; poles are removable.
    val = (0.75 * np.sinc(x)
           + 0.5 * (np.sinc(x - 1.0) + np.sinc(x + 1.0))
           + 0.125 * (np.sinc(x - 2.0) + np.sinc(x + 2.0)))
    return float(val) if np.ndim(q) == 0 else val


def chi_hat(k, delta, center):
    _finite(delta, center)
    if not (delta > 0):
        raise ValueError('nonpositive delta')
    k_arr = np.asarray(k, dtype=np.float64)
    _finite(k_arr)
    val = delta * np.exp(-1j * k_arr * center) * g(k_arr * delta)
    return complex(val) if np.ndim(k) == 0 else val


def response_q(a, Q, h_max):
    _finite(a, Q, h_max)
    n = even_panel_count(Q - a, h_max)
    q = np.linspace(a, Q, n + 1)
    integrand = (q - a) * g(q) ** 2 / (4.0 * math.pi ** 2)
    return float(composite_simpson(integrand, (Q - a) / n)), n


def response_omega(E, delta, center, Q, h_max):
    _finite(E, delta, center, Q, h_max)
    if not (delta > 0):
        raise ValueError('nonpositive delta')
    a = E * delta
    omega_max = (Q - a) / delta
    n = even_panel_count(omega_max, h_max / delta)
    omega = np.linspace(0.0, omega_max, n + 1)
    chi = chi_hat(E + omega, delta, center)
    integrand = omega * np.abs(chi) ** 2 / (4.0 * math.pi ** 2)
    return float(composite_simpson(integrand, omega_max / n)), n


def tail_bound(Q):
    _finite(Q)
    return 64.0 * math.pi ** 6 / (75.0 * Q ** 8)


def load_chi_fn(source, expected_sha256):
    sys.dont_write_bytecode = True
    source = Path(source)
    raw = source.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError('upstream source pin mismatch')
    spec = importlib.util.spec_from_file_location('published_switching', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.ChiFn


def direct_fourier(chi, k, panels=8192):
    _finite(k, panels)
    n = panels if panels % 2 == 0 else panels + 1
    tau0, tau1 = float(chi.tau0), float(chi.tau1)
    tau = np.linspace(tau0, tau1, n + 1)
    integrand = chi(tau) * np.exp(-1j * k * tau)
    return composite_simpson(integrand, (tau1 - tau0) / n)


def _rejects(fn):
    try:
        fn()
    except ValueError:
        return True
    return False


def run(source, expected_sha256):
    start = time.perf_counter()
    chi_cls = load_chi_fn(source, expected_sha256)
    source_sha = hashlib.sha256(Path(source).read_bytes()).hexdigest()
    candidate_sha = hashlib.sha256(CANDIDATE.read_bytes()).hexdigest()

    g_pole_rows = []
    g_poles_ok = True
    for q, expected in POLE_G.items():
        value = g(q)
        err = abs(value - expected)
        ok = err <= 1e-12
        g_poles_ok = g_poles_ok and ok
        g_pole_rows.append({'q': q, 'g': value, 'expected': expected, 'error': err, 'passed': ok})

    even_rows = []
    even_ok = True
    sample = np.concatenate([np.array(POLES), np.linspace(-13.2, 13.2, 265)])
    for q in sample:
        left, right = g(float(-q)), g(float(q))
        err = abs(left - right)
        ok = err <= 1e-12
        even_ok = even_ok and ok
        even_rows.append({'q': float(q), 'g_minus': left, 'g_plus': right, 'error': err, 'passed': ok})

    neighbor_rows = []
    neighbors_ok = True
    for pole, expected in POLE_G.items():
        for shift in (1e-8, -1e-8):
            q = pole + shift
            value = g(q)
            err = abs(value - expected)
            ok = math.isfinite(value)
            neighbors_ok = neighbors_ok and ok
            neighbor_rows.append({'q': q, 'g': value, 'expected': expected, 'error': err, 'passed': ok})

    transform_rows = []
    transform_ok = True
    settings = ((1.0, 0.0), (0.125, 1.25))
    for delta, center in settings:
        chi = chi_cls(center, delta)
        for q in TRANSFORM_Q:
            k = q / delta
            formula = chi_hat(k, delta, center)
            direct = direct_fourier(chi, k)
            err = abs(direct - formula)
            ok = err <= 1e-10
            transform_ok = transform_ok and ok
            transform_rows.append({
                'q': q, 'delta': delta, 'center': center, 'k': k,
                'direct_real': float(np.real(direct)), 'direct_imag': float(np.imag(direct)),
                'formula_real': float(np.real(formula)), 'formula_imag': float(np.imag(formula)),
                'abs_error': float(err), 'passed': bool(ok)})

    rejection_rows = [
        {'case': 'chi_hat nan delta', 'rejected': _rejects(lambda: chi_hat(1.0, math.nan, 0.0))},
        {'case': 'chi_hat inf delta', 'rejected': _rejects(lambda: chi_hat(1.0, math.inf, 0.0))},
        {'case': 'chi_hat zero delta', 'rejected': _rejects(lambda: chi_hat(1.0, 0.0, 0.0))},
        {'case': 'chi_hat negative delta', 'rejected': _rejects(lambda: chi_hat(1.0, -1.0, 0.0))},
        {'case': 'g nan', 'rejected': _rejects(lambda: g(math.nan))},
        {'case': 'response_q inf a', 'rejected': _rejects(lambda: response_q(math.inf, Q_FINE, H_MAX[0]))},
        {'case': 'response_omega nonpositive delta',
         'rejected': _rejects(lambda: response_omega(1.0, 0.0, 0.0, Q_FINE, H_MAX[0]))},
        {'case': 'chi_hat nonfinite k', 'rejected': _rejects(lambda: chi_hat(math.nan, 1.0, 0.0))},
        {'case': 'chi_hat nonfinite center', 'rejected': _rejects(lambda: chi_hat(1.0, 1.0, math.inf))},
    ]
    rejection_ok = all(row['rejected'] for row in rejection_rows)

    cases = []
    panel_counts = []
    discrepancies = []
    positivity_ok = True
    refine_ok = True
    double_ok = True
    tail_ok = True
    dimensional_ok = True
    phase_ok = True
    for a in A_VALUES:
        values, panels = [], []
        for h_max in H_MAX:
            value, n = response_q(a, Q_FINE, h_max)
            values.append(value)
            panels.append(n)
        F_double, n_double = response_q(a, Q_DOUBLE, H_MAX[-1])
        F_finest = values[-1]
        T = 1e-8 + 1e-6 * abs(F_finest)
        d16_32 = abs(values[0] - values[1])
        d32_64 = abs(values[1] - values[2])
        dQ = abs(F_finest - F_double)
        finite_nn = all(math.isfinite(v) and v >= 0.0 for v in values + [F_double])
        positivity_ok = positivity_ok and finite_nn
        refine_case = d16_32 <= T / 4 and d32_64 <= T / 4
        double_case = dQ <= T / 4
        refine_ok = refine_ok and refine_case
        double_ok = double_ok and double_case
        bound = tail_bound(Q_FINE)
        tail_case = (Q_FINE >= max(4 * math.pi, 2 * abs(a))) and bound <= T / 4
        tail_ok = tail_ok and tail_case
        dim_rows = []
        for delta in DELTAS:
            for center in CENTERS:
                E = a / delta
                F_om, n_om = response_omega(E, delta, center, Q_FINE, H_MAX[-1])
                omega_max = (Q_FINE - a) / delta
                omega = np.linspace(0.0, omega_max, n_om + 1)
                chi = chi_hat(E + omega, delta, center)
                phase_err = float(np.max(np.abs(np.abs(chi) ** 2 - (delta ** 2) * g((E + omega) * delta) ** 2)))
                dim_err = abs(F_om - F_finest)
                dim_pass = dim_err <= T / 4
                phase_pass = phase_err <= 1e-12
                dimensional_ok = dimensional_ok and dim_pass
                phase_ok = phase_ok and phase_pass
                dim_rows.append({
                    'delta': delta, 'center': center, 'E': E, 'F_omega': F_om, 'panels': n_om,
                    'discrepancy_vs_dimensionless': dim_err, 'phase_cancellation_max_abs': phase_err,
                    'passed': dim_pass, 'phase_cancellation_passed': phase_pass})
        row = {
            'a': a, 'F_finest': F_finest, 'T': T,
            'F_values': {'h_1_16': values[0], 'h_1_32': values[1], 'h_1_64': values[2],
                         'Q_128_h_1_64': F_double},
            'panels': {'h_1_16': panels[0], 'h_1_32': panels[1], 'h_1_64': panels[2],
                       'Q_128_h_1_64': n_double},
            'discrepancies': {'refine_1_16_to_1_32': d16_32, 'refine_1_32_to_1_64': d32_64,
                              'Q_64_to_128': dQ, 'T_over_4': T / 4},
            'tail_bound_Q64': bound, 'tail_passed': tail_case,
            'finite_nonnegative': finite_nn, 'refinement_passed': refine_case,
            'q_doubling_passed': double_case, 'dimensional': dim_rows}
        cases.append(row)
        panel_counts.append({'a': a, **row['panels']})
        discrepancies.append({'a': a, **row['discrepancies']})

    analytic_rows = []
    analytic_ok = True
    by_a = {row['a']: row for row in cases}
    for a in (1.0, 4.0):
        left, right = by_a[-a], by_a[a]
        diff = left['F_finest'] - right['F_finest']
        expected = 35.0 * a / (128.0 * math.pi)
        Tsum = left['T'] + right['T']
        err = abs(diff - expected)
        ok = err <= Tsum
        analytic_ok = analytic_ok and ok
        analytic_rows.append({
            'a': a, 'F_minus_a': left['F_finest'], 'F_a': right['F_finest'],
            'difference': diff, 'expected_35a_over_128pi': expected,
            'error': err, 'T_sum': Tsum, 'passed': ok})

    elapsed = time.perf_counter() - start
    findings = {
        'positivity_finiteness': positivity_ok,
        'grid_refinement': refine_ok,
        'q_doubling': double_ok,
        'g_poles': g_poles_ok,
        'g_evenness': even_ok,
        'pole_neighbors': neighbors_ok,
        'direct_transform': transform_ok,
        'rejection': rejection_ok,
        'dimensional': dimensional_ok,
        'phase_cancellation': phase_ok,
        'tail': tail_ok,
        'analytic_difference': analytic_ok,
        'chi_fn_unchanged': source_sha == expected_sha256,
        'all_passed': all((positivity_ok, refine_ok, double_ok, g_poles_ok, even_ok,
                           neighbors_ok, transform_ok, rejection_ok, dimensional_ok,
                           phase_ok, tail_ok, analytic_ok, source_sha == expected_sha256))}
    return {
        'kind': 'inertial Minkowski vacuum detector-response baseline, not Hawking radiation or FPM advantage',
        'paper': 'https://arxiv.org/html/2501.06609v2#S3.SS1',
        'source': str(Path(source)),
        'source_sha256': source_sha,
        'candidate_sha256': candidate_sha,
        'frozen_decision_sha256': 'c730771bdfd12f7ec2f48c6f5d20475b105c0b2927fb800a3cfc503ff7ceb3c9',
        'units_conventions': {
            'hbar': 1, 'c': 1,
            'F': 'dimensionless leading-order response; coupling and detector matrix-element factors divided out; not a probability',
            'Fourier': 'chi_hat(k) = integral chi(tau) exp(-i k tau) d tau',
            'chi_hat': 'delta * exp(-i k center) * g(k * delta)',
            'sinc': 'sin(pi x)/(pi x)',
            'a': 'E * delta',
            'quadrature': 'composite Simpson; even panel count; max step rounded from 1/16, 1/32, 1/64',
            'omega_measure': 'omega d omega / (4 pi^2)'},
        'parameters': {
            'a': list(A_VALUES), 'Q': Q_FINE, 'Q_double': Q_DOUBLE, 'h_max': list(H_MAX),
            'delta': list(DELTAS), 'center': list(CENTERS), 'transform_q': list(TRANSFORM_Q),
            'g_pole_tolerance': 1e-12, 'transform_tolerance': 1e-10,
            'numerical_timeout_seconds': 60, 'fourier_panels': 8192},
        'environment': {'python': platform.python_version(), 'numpy': np.__version__,
                         'platform': platform.platform()},
        'elapsed_seconds': elapsed,
        'cases': cases,
        'panel_counts': panel_counts,
        'discrepancies': discrepancies,
        'g_poles': g_pole_rows,
        'g_evenness': even_rows,
        'pole_neighbors': neighbor_rows,
        'direct_transform': transform_rows,
        'rejection': rejection_rows,
        'analytic_difference': analytic_rows,
        'findings': findings}


def jsonable(obj):
    if isinstance(obj, dict):
        return {key: jsonable(value) for key, value in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [jsonable(value) for value in obj]
    if isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.complexfloating, complex)):
        return {'real': float(obj.real), 'imag': float(obj.imag)}
    return obj


def main_write(source, expected_sha256, output):
    output = Path(output)
    if output.exists():
        raise SystemExit('output must be new')
    result = jsonable(run(source, expected_sha256))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    print(json.dumps({'all_passed': result['findings']['all_passed'],
                       'elapsed_seconds': result['elapsed_seconds']}, indent=2))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('expected_sha256')
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    main_write(args.source, args.expected_sha256, args.output)
    sys.exit(0)
