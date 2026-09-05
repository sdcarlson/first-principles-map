"""Astra review of saved candidate evidence; no response integrations are rerun."""
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    result_path, output = map(Path, sys.argv[1:])
    if output.exists():
        raise ValueError('Review output must be new')
    here = Path(__file__).resolve().parent
    research = here.parents[1]
    candidate = research / 'vacuum_baseline.py'
    reference_path = here / 'result.json'
    data = json.loads(result_path.read_bytes())
    reference = json.loads(reference_path.read_bytes())
    checks = []

    def check(name, passed, detail=None):
        checks.append(dict(name=name, passed=bool(passed), detail=detail))

    check('candidate source pin', sha(candidate) == data['candidate_sha256'])
    check('original source pin', data['source_sha256'] == reference['source_sha256'])
    check('frozen decision pin', data['frozen_decision_sha256'] == reference['frozen_decision_sha256'])
    check('independent reviewer source pin', sha(here / 'reviewer.py') == reference['checker_sha256'])
    check('five gaps', sorted(x['a'] for x in data['cases']) == [-4, -1, 0, 1, 4])
    responses = []
    for row in data['cases']:
        a, f = row['a'], row['F_finest']
        tolerance = 1e-8 + 1e-6 * abs(f)
        values = row['F_values']
        changes = [abs(values['h_1_16']-values['h_1_32']),
                   abs(values['h_1_32']-values['h_1_64']),
                   abs(values['h_1_64']-values['Q_128_h_1_64'])]
        check(f'finite nonnegative {a}', all(math.isfinite(v) and v >= 0 for v in values.values()))
        check(f'finest and tolerance {a}', f == values['h_1_64'] and row['T'] == tolerance)
        check(f'refinements and cutoff {a}', all(d <= tolerance/4 for d in changes), changes)
        expected_panels = {'h_1_16': int((64-a)*16), 'h_1_32': int((64-a)*32),
                           'h_1_64': int((64-a)*64), 'Q_128_h_1_64': int((128-a)*64)}
        check(f'actual panel counts {a}', row['panels'] == expected_panels, row['panels'])
        bound = 64*math.pi**6/(75*64**8)
        check(f'analytic tail {a}', 64 >= max(4*math.pi, 2*abs(a)) and
              row['tail_bound_Q64'] == bound and bound <= tolerance/4, bound)
        ref = next(x for x in reference['rows'] if x['a'] == a)
        change = abs(f-ref['outer32_inner512'])
        check(f'independent response {a}', change <= tolerance, change)
        check(f'independent refinements {a}', ref['inner_change'] <= tolerance/4 and ref['outer_change'] <= tolerance/4)
        dims = row['dimensional']
        check(f'scale and center coverage {a}', sorted((d['delta'],d['center']) for d in dims) ==
              [(d,c) for d in (0.125,1,4) for c in (0,1.25)])
        check(f'dimensional response {a}', all(d['E'] == a/d['delta'] and
              math.isfinite(d['F_omega']) and abs(d['F_omega']-f) <= tolerance/4 and
              d['panels'] == expected_panels['h_1_64'] for d in dims))
        responses.append(dict(a=a, candidate=f, independent=ref['outer32_inner512'],
                              discrepancy=change, tolerance=tolerance))
    saved_g = {r['q']:r['g'] for r in data['g_poles'] + data['pole_neighbors']}
    saved_g.update({r['q']:r['formula_real'] for r in data['direct_transform']
                    if r['delta'] == 1 and r['center'] == 0})
    transforms = []
    for ref in reference['transform_samples']:
        q = ref['q']
        error = abs(saved_g[q]-ref['direct_g']) if q in saved_g else None
        check(f'independent original-ChiFn transform {q}', error is not None and error <= 1e-10, error)
        transforms.append(dict(q=q, discrepancy=error))
    check('special values', all(abs(r['g']-r['expected']) <= 1e-12 for r in data['g_poles']))
    check('evenness', all(abs(r['g_minus']-r['g_plus']) <= 1e-12 for r in data['g_evenness']))
    check('candidate direct Fourier checks', all(r['abs_error'] <= 1e-10 for r in data['direct_transform']))
    by_a = {r['a']:r for r in data['cases']}
    for a in (1,4):
        error = abs(by_a[-a]['F_finest']-by_a[a]['F_finest']-35*a/(128*math.pi))
        check(f'Parseval response difference {a}', error <= by_a[-a]['T']+by_a[a]['T'], error)
    # Source was inspected before this import. Only input-rejection calls execute.
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location('inspected_candidate', candidate)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    invalid = []
    signatures = [('g',[1.0]), ('chi_hat',[1.0,1.0,0.0]),
                  ('response_q',[1.0,64.0,1/16]), ('response_omega',[1.0,1.0,0.0,64.0,1/16])]
    for name, args in signatures:
        for pos in range(len(args)):
            for bad in (math.nan, math.inf, -math.inf):
                values = list(args)
                values[pos] = bad
                try:
                    getattr(module,name)(*values)
                    rejected = False
                except ValueError:
                    rejected = True
                invalid.append(dict(function=name, parameter=pos, input=str(bad), rejected=rejected))
    for name, args in signatures:
        if name not in ('chi_hat','response_omega'):
            continue
        for bad in (0,-1):
            values = list(args)
            values[1] = bad
            try:
                getattr(module,name)(*values)
                rejected = False
            except ValueError:
                rejected = True
            invalid.append(dict(function=name,parameter=1,input=str(bad),rejected=rejected))
    check('all nonfinite inputs and nonpositive durations', all(r['rejected'] for r in invalid), len(invalid))
    report = dict(reviewer='Astra local independent review; not a registered physics checker',
                  candidate_sha256=sha(candidate), candidate_result_sha256=sha(result_path),
                  reference_result_sha256=sha(reference_path), audit_source_sha256=sha(Path(__file__)),
                  frozen_decision_sha256=reference['frozen_decision_sha256'],
                  response_comparisons=responses, transform_comparisons=transforms,
                  invalid_input_cases=invalid, checks=checks,
                  mathematical_checks_passed=all(c['passed'] for c in checks),
                  formal_acceptance='withheld; no registered independent physics checker',
                  limitation='Saved numerical evidence plus inspected formulas and invalid-input calls; no response integration repeated. Quadrature refinement is empirical. This does not establish domain certification or structured-state value.')
    with output.open('x', encoding='utf-8') as stream:
        json.dump(report,stream,indent=2,allow_nan=False)
        stream.write('\n')
    print(json.dumps(dict(passed=report['mathematical_checks_passed'],checks=len(checks),
                          failed=[c for c in checks if not c['passed']]),indent=2))


if __name__ == '__main__':
    main()
