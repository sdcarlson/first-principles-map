"""Package the observed, limited physics reproduction for a fresh recipient."""
import argparse
from pathlib import Path
import sys
import handoff as h


def prepare(upstream, destination):
    upstream, destination = Path(upstream), Path(destination)
    h.require(not destination.exists(), 'physics package destination must be new')
    store = destination / 'store'; inbox = destination / 'original-evidence'
    inbox.mkdir(parents=True)
    files = {
        'switching.py': upstream / 'hawkrad/switching.py',
        'upstream-license.txt': upstream / 'LICENSE',
        'reproduction.py': h.HERE / 'physics_prerequisite.py',
        'result.json': h.HERE / 'evidence/physics-switching.json',
    }
    for name, path in files.items(): h.create_file(inbox / name, path.read_bytes())
    shared_inputs = {}
    for name in ('switching.py', 'upstream-license.txt'):
        raw = (inbox / name).read_bytes()
        key = h.digest(raw)
        h.create_file(store / 'artifacts' / key, raw)
        shared_inputs[name] = key
    result = h.read_json(inbox / 'result.json')
    h.require(result['source_sha256'] == h.digest((inbox / 'switching.py').read_bytes()), 'source provenance mismatch')
    target = {
        'id': 'hawking-detector-switching', 'owner': 'Seth, exploratory learning; domain reviewer not appointed',
        'question': 'Can we reproduce the detector switching normalization before studying near-horizon quantum response?',
        'scope': 'Published-code prerequisite only: compact cos^4 switching, not Hawking radiation or quantum gravity.',
        'assumptions': 'Positive half-duration delta; proper time; published switching function. Known analytic identities, not a frontier result.',
        'acceptance': {'checker': 'external-review-pending', 'checker_sha256': None,
                       'criterion': 'Review original upstream bytes and reproduce support, peak, integral chi=3 delta/4 and integral chi^2=35 delta/64 at both grids. Confirm tolerances and meaning independently before acceptance.'},
        'inputs': {'files': shared_inputs, 'paper': result['paper'], 'source_sha256': result['source_sha256'],
                   'source_commit': '7bf91b9517cfd4f136fb13a98f0a2aee7e903ca4',
                   'public_code': 'https://github.com/cshallue/hawking-radiation'},
        'stop_condition': 'Reproduce only this prerequisite. No full mode sum, external calls or inference of FPM advantage.',
        'provenance': 'User selected quantum mechanics and relativity; assistant located public authors and code. No research partner recruited.'}
    target_key = h.add_target(store, target)
    submission = {
        'request_id': 'switching-reproduction-1', 'base_snapshot': h.snapshot(store), 'target': target_key,
        'method': 'Run published ChiFn; composite trapezoidal quadrature against separate analytic integrals.',
        'scope': target['scope'],
        'inputs': {'tau_mid': [0, 1.25], 'delta': [0.125, 1, 4], 'panels': [512, 1024]},
        'environment': str(result['environment']),
        'budget': {'measured_numerical_seconds': result['elapsed_seconds'], 'human_minutes': None, 'compute_usd': None},
        'outcome': 'completed', 'observation': 'All twelve parameter/grid checks passed. Original numerical outputs attached.',
        'interpretation': 'This supports only the sampled switching normalization. The detector response and paper conclusions remain untested.',
        'retry_reason': 'Replication is allowed; it is not a new contribution. Changed durations/units or later response calculations need their own scope.',
        'depends_on': [],
        'provenance': {'contributor': 'local-python-reproduction', 'model': 'none in numerical execution',
                       'configuration': 'Python 3.12.14; NumPy 2.3.5; not the full upstream Conda environment',
                       'source_locator': 'hawkrad/switching.py:5-20; paper equations 9-13',
                       'shared_roots': 'Same source and local analyst; analytic and numerical methods differ; no external human verification.'},
        'evidence': [{'path': name, 'role': 'result' if name == 'result.json' else 'source',
                      'source': 'original local run or pinned upstream source', 'locator': 'entire file'} for name in files]}
    h.create_file(inbox / 'submission.json', h.encoded(submission))
    attempt = h.submit(store, inbox / 'submission.json')
    assessment = h.assess(store, attempt, 'GPT-6 Astra task analyst (requested configuration)', 'withhold',
                          'Numerical prerequisite passed the recorded local checks. Formal research acceptance awaits independent domain review.',
                          'No full Hawking calculation, scientific discovery, blinded usefulness review, or FPM experiment. Model identity here is a provenance label, not backend attestation.')
    brief = {
        'current_assessment': 'The published detector-switching function passed twelve local normalization checks. Scientific acceptance remains withheld pending an independent review; original code, license and numerical output are attached.',
        'unresolved_checks': 'This says nothing yet about the full quantum-field response near a horizon. The full calculation needs SciPy, absl-py and asymptotic coefficient data, and its convergence and compute cost must be assessed. No original multi-person handoff history or design partner is available.',
        'proposed_next_check': 'Review the two analytic normalization identities against the attached numerical output without asking the previous author. If sound, next scope the flat-spacetime detector-response baseline before a curved-spacetime mode sum. Record all preparation and review minutes.'}
    h.create_file(destination / 'brief.json', h.encoded(brief))
    for arm in 'ABCD': h.export(store, target_key, destination / arm, arm, brief)
    result = {'target': target_key, 'attempt': attempt, 'assessment': assessment,
              'status': 'withheld; observed prerequisite, not a scientific-value or customer-demand result',
              'next_input': 'C/handoff.md', 'structured_comparison': 'D/state.json'}
    h.create_file(destination / 'index.json', h.encoded(result))
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('upstream', type=Path); p.add_argument('destination', type=Path)
    args = p.parse_args()
    print(h.encoded(prepare(args.upstream, args.destination)).decode('utf-8'))
