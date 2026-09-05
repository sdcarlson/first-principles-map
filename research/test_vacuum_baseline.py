"""Focused numerical tests for the frozen inertial vacuum baseline contract."""
import hashlib
import inspect
import json
import math
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

import numpy as np

import vacuum_baseline as vb


HERE = Path(__file__).resolve().parent
SWITCHING = HERE / 'physics/C/inputs/switching.py'
SWITCHING_SHA256 = 'f948c9be21949f84e1679ab380dde6553183782bdc46f4be8c7a8845da732a68'
POLES = (0.0, math.pi, -math.pi, 2 * math.pi, -2 * math.pi)
POLE_G = {0.0: 0.75, math.pi: 0.5, -math.pi: 0.5, 2 * math.pi: 0.125, -2 * math.pi: 0.125}


class VacuumBaselineTests(unittest.TestCase):
    def test_g_uses_stable_sinc_expansion_at_removable_poles(self):
        source = inspect.getsource(vb.g)
        self.assertIn('sinc', source)
        for q, expected in POLE_G.items():
            self.assertAlmostEqual(vb.g(q), expected, delta=1e-12)

    def test_g_is_even_and_finite_near_poles(self):
        for q in (0.0, 0.37, math.pi, 2 * math.pi, 7.1):
            self.assertAlmostEqual(vb.g(-q), vb.g(q), delta=1e-14)
        for pole, expected in POLE_G.items():
            for shift in (1e-8, -1e-8):
                value = vb.g(pole + shift)
                self.assertTrue(math.isfinite(value))
                self.assertAlmostEqual(vb.g(-(pole + shift)), value, delta=1e-12)

    def test_new_boundary_rejects_nonfinite_inputs_and_nonpositive_delta(self):
        chi_cls = vb.load_chi_fn(SWITCHING, SWITCHING_SHA256)
        self.assertEqual(hashlib.sha256(SWITCHING.read_bytes()).hexdigest(), SWITCHING_SHA256)
        chi_cls(0.0, 1.0)(np.array([0.0]))
        for bad in (math.nan, math.inf, -math.inf, 0.0, -1.0):
            with self.assertRaises(ValueError):
                vb.chi_hat(1.0, bad, 0.0)
        for bad in (math.nan, math.inf, -math.inf):
            with self.assertRaises(ValueError):
                vb.g(bad)
            with self.assertRaises(ValueError):
                vb.response_q(bad, 64.0, 1.0 / 16.0)
            with self.assertRaises(ValueError):
                vb.chi_hat(bad, 1.0, 0.0)
            with self.assertRaises(ValueError):
                vb.response_omega(bad, 1.0, 0.0, 64.0, 1.0 / 16.0)

    def test_simpson_panels_are_even_and_respect_max_step(self):
        length = 64.0 - 4.0
        for h_max in (1.0 / 16.0, 1.0 / 32.0, 1.0 / 64.0):
            n = vb.even_panel_count(length, h_max)
            self.assertEqual(n % 2, 0)
            self.assertGreaterEqual(n, 2)
            self.assertLessEqual(length / n, h_max + 1e-15)

    def test_dimensional_response_integrates_omega_and_complex_chi_hat(self):
        source = inspect.getsource(vb.response_omega)
        self.assertIn('omega', source)
        self.assertIn('chi_hat', source)
        self.assertIn('exp', inspect.getsource(vb.chi_hat))
        self.assertNotIn('response_q', source)
        original = vb.chi_hat
        a, Q, h_max, delta, center = 1.0, 64.0, 1.0 / 16.0, 1.0, 1.25
        baseline, _ = vb.response_omega(a / delta, delta, center, Q, h_max)
        try:
            vb.chi_hat = lambda k, d, c: 2 * original(k, d, c)
            scaled, _ = vb.response_omega(a / delta, delta, center, Q, h_max)
        finally:
            vb.chi_hat = original
        self.assertGreater(scaled, 3.5 * baseline)
        dimensionless, _ = vb.response_q(a, Q, h_max)
        T = 1e-8 + 1e-6 * abs(dimensionless)
        self.assertLessEqual(abs(baseline - dimensionless), T / 4)

    def test_run_records_raw_contract_arrays_even_if_a_check_fails(self):
        result = vb.run(SWITCHING, SWITCHING_SHA256)
        for key in ('cases', 'panel_counts', 'discrepancies', 'units_conventions',
                    'parameters', 'source_sha256', 'candidate_sha256',
                    'environment', 'elapsed_seconds', 'findings'):
            self.assertIn(key, result)
        self.assertEqual(len(result['cases']), 5)
        self.assertEqual(result['source_sha256'], SWITCHING_SHA256)
        self.assertEqual(result['candidate_sha256'],
                         hashlib.sha256((HERE / 'vacuum_baseline.py').read_bytes()).hexdigest())
        self.assertEqual(set(x['a'] for x in result['cases']), {-4.0, -1.0, 0.0, 1.0, 4.0})
        for row in result['cases']:
            self.assertIn('F_values', row)
            self.assertIn('panels', row)
            self.assertTrue(math.isfinite(row['F_finest']))
            self.assertGreaterEqual(row['F_finest'], 0.0)
        self.assertIsInstance(result['findings']['all_passed'], bool)
        self.assertIn('python', result['environment'])
        self.assertGreater(result['elapsed_seconds'], 0.0)
        self.assertTrue(result['findings']['all_passed'], result['findings'])

    def test_cli_uses_new_output_path_and_external_timeout(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'result.json'
            t0 = time.perf_counter()
            done = subprocess.run(
                [sys.executable, str(HERE / 'vacuum_baseline.py'),
                 str(SWITCHING), SWITCHING_SHA256, str(out)],
                capture_output=True, timeout=60, cwd=str(HERE), text=True)
            elapsed = time.perf_counter() - t0
            self.assertLess(elapsed, 60)
            self.assertEqual(done.returncode, 0, done.stderr)
            self.assertTrue(out.is_file())
            payload = json.loads(out.read_text(encoding='utf-8'))
            self.assertIn('findings', payload)
            with self.assertRaises(SystemExit):
                vb.main_write(SWITCHING, SWITCHING_SHA256, out)


if __name__ == '__main__':
    unittest.main()
