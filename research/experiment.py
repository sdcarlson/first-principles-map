"""Prepare four conditions and exercise their mechanics without model spending."""
import argparse
import itertools
import json
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys
import time

import handoff as h

HERE = Path(__file__).resolve().parent
LABOR_FIELDS = ('preparation', 'curation', 'review', 'correction', 'maintenance')
METRICS = ('useful_progress_units', 'avoidable_duplicate_executions', 'known_error_recurrence',
           'false_prerequisite_downstream_acceptance', 'unsupported_acceptance',
           'valid_approaches', 'harmful_exclusions', 'first_useful_check_seconds',
           'author_interventions', 'checked_progress_depth')


def fixture_target(n=5):
    return {'id': 'fixture-cycle-' + str(n), 'owner': 'local mechanics test',
            'question': 'Construct a simple regular triangle-free graph on the specified vertices.',
            'scope': 'SOFTWARE FIXTURE ONLY. Labeled finite graph, not a research problem.',
            'assumptions': 'Vertices 0..n-1; undirected edges; degree two.',
            'acceptance': {'checker': 'fixture-graph-v1',
                           'checker_sha256': h.digest(h.CHECKER.read_bytes()),
                           'criterion': {'n': n, 'degree': 2, 'triangle_free': True}},
            'inputs': {'vertices': list(range(n)), 'external_corpus': []},
            'stop_condition': 'One result or five seconds; no model/API calls.',
            'provenance': 'Invented software test; no scientific history or customer evidence.'}


def draft(store, target, request_id, result_path='result.json', outcome='completed', depends_on=None):
    return {'request_id': request_id, 'base_snapshot': h.snapshot(store), 'target': target,
            'method': 'Cycle construction', 'scope': 'The fixed finite graph fixture only.',
            'inputs': {'target_digest': target}, 'environment': 'Python standard library; deterministic fixture',
            'budget': {'model_tokens': 0, 'wall_seconds_cap': 5}, 'outcome': outcome,
            'observation': 'Original candidate is attached for independent checking.',
            'interpretation': 'No impossibility or scientific novelty claim.',
            'retry_reason': 'An incomplete path does not rule out closing the cycle; unchanged repetition is replication.',
            'depends_on': depends_on or [],
            'provenance': {'contributor': 'fixture-worker', 'model': 'none',
                           'configuration': 'deterministic local program',
                           'source_locator': 'fixture_worker.py',
                           'shared_roots': 'All workers use the same constructor; NOT independent methods.'},
            'evidence': [{'path': result_path, 'role': 'result',
                          'source': 'local fixture execution', 'locator': 'entire JSON candidate'}]}


def seed(store, inbox, n=5):
    target = h.add_target(store, fixture_target(n))
    inbox = Path(inbox); inbox.mkdir(parents=True, exist_ok=False)
    h.create_file(inbox / 'result.json', h.encoded({'edges': [[i, i+1] for i in range(n-1)]}))
    h.create_file(inbox / 'original-log.txt', b'FICTIONAL HISTORY FOR TESTING: path construction stopped before closing edge. This does not show that cycles are impossible. Retry with a closing edge.\n')
    submission = draft(store, target, 'seed-incomplete', outcome='incomplete')
    submission['evidence'].append({'path': 'original-log.txt', 'role': 'execution_log',
                                   'source': 'explicitly invented fixture', 'locator': 'entire log'})
    h.create_file(inbox / 'submission.json', h.encoded(submission))
    attempt = h.submit(store, inbox / 'submission.json')
    receipt = h.check_attempt(store, attempt)
    assessment = h.assess(store, attempt, 'fixture-reviewer', 'withhold',
                          'The path has endpoints of degree one. Execution was incomplete; retry is justified.',
                          'This failure is about the submitted path only. Fixture labels are not human reviews.', receipt)
    return target, attempt, assessment


def brief(store, target):
    view = h.inspect_target(store, target)
    return {'current_assessment': 'The original path stopped before its closing edge. This is an incomplete execution, not evidence against cycles. All material assessments remain in the attached record.',
            'unresolved_checks': 'Check both endpoint degrees, absence of triangles and exact vertex scope. Repeated copies of an accepted result are replication, not new progress. There are '
                                  + str(len(view['attempts'])) + ' retained attempts in this condition.',
            'proposed_next_check': 'For this mechanics fixture, close the path into a cycle and submit the original edge list. A pass establishes only these finite graph constraints; a failure identifies a candidate defect. Do not infer a scientific benefit for FPM.'}


def demo(destination, arms='ABCD', tasks=1, episodes=3):
    destination = Path(destination)
    h.require(not destination.exists(), 'demo destination must be new; previous evidence is preserved')
    destination.mkdir(parents=True)
    ledger = []
    for task in range(tasks):
        seed_store = destination / f'task-{task+1}' / 'frozen-seed' / 'store'
        target, _, _ = seed(seed_store, seed_store.parent / 'original', 5 + task)
        for arm in arms:
            chain = destination / f'task-{task+1}' / arm
            store = chain / 'store'
            shutil.copytree(seed_store, store)
            for episode in range(episodes):
                # A starts every episode with only the target; other conditions keep this chain only.
                episode_store = store
                if arm == 'A':
                    episode_store = chain / f'fresh-store-{episode+1}'
                    target = h.add_target(episode_store, fixture_target(5 + task))
                package = chain / f'episode-{episode+1}' / 'input'
                info = h.export(episode_store, target, package, arm, brief(episode_store, target))
                # Complete raw history retrieval is available to every history condition.
                retrieved = h.retrieve(package, 'path closing') if arm != 'A' else []
                start = time.perf_counter()
                done = subprocess.run([sys.executable, '-I', str(HERE / 'fixture_worker.py'), str(package.resolve())],
                                      capture_output=True, timeout=5, cwd=package,
                                      env={k: os.environ[k] for k in ('SYSTEMROOT', 'WINDIR') if k in os.environ})
                elapsed = time.perf_counter() - start
                h.require(done.returncode == 0, 'fixture worker failed: ' + done.stderr.decode('utf-8', errors='replace'))
                output = json.loads(done.stdout)
                inbox = package.parent / 'output'; inbox.mkdir()
                h.create_file(inbox / 'worker-output.json', done.stdout)
                h.create_file(inbox / 'result.json', h.encoded(output['candidate']))
                submission = draft(episode_store, target, f'episode-{episode+1}')
                submission['evidence'].append({'path': 'worker-output.json', 'role': 'execution_log',
                                               'source': 'fresh deterministic process stdout', 'locator': 'entire output'})
                h.create_file(inbox / 'submission.json', h.encoded(submission))
                attempt = h.submit(episode_store, inbox / 'submission.json')
                check = h.check_attempt(episode_store, attempt)
                assessment = h.assess(episode_store, attempt, 'fixture-check-reviewer', 'accept',
                                      'The separate finite-graph checker passed.',
                                      'Only software mechanics verified. Scientific usefulness unassessed.', check)
                ledger.append({'task': task+1, 'condition': arm, 'episode': episode+1,
                               'fixture': True, 'attempt': attempt, 'check': check, 'assessment': assessment,
                               'target': target, 'input_snapshot': info['base_snapshot'],
                               'process_seconds': elapsed, 'retrieved_documents': len(retrieved),
                               'model_tokens': 0, 'model_cost_usd': 0,
                               'local_compute_cost_usd': None,
                               'human_minutes': {name: None for name in LABOR_FIELDS},
                               'metrics': {name: None for name in METRICS},
                               'gate': 'ineligible: deterministic fixture; unknown labor; no scientific usefulness judgment'})
    h.create_file(destination / 'ledger.json', h.encoded(ledger))
    result = {'fixture': True, 'checked_episodes': len(ledger),
              'conditions': list(arms), 'research_experiment_run': False,
              'interpretation': 'All condition mechanics ran; no hypothesis estimate or adoption evidence.'}
    h.create_file(destination / 'result.json', h.encoded(result))
    return result


def schedule(task_ids, families, seed_value=20260905):
    h.require(len(task_ids) in {4, 12, 24} and len(set(task_ids)) == len(task_ids),
              'use four feasibility tasks, twelve screen tasks, or preregistered extension to 24')
    h.require(len(families) == 3 and len(set(families)) == 3, 'three distinct actual model families required')
    orders = list(itertools.permutations(families))
    rng = random.Random(seed_value)
    blocks = [(task, block) for task in task_ids for block in (1, 2)]
    rng.shuffle(blocks)
    rows = []
    for i, (task, block) in enumerate(blocks):
        order = orders[i % 6]
        arms = list('ABCD'); rng.shuffle(arms)
        for arm in arms:
            for episode, family in enumerate(order, 1):
                rows.append({'task': task, 'block': block, 'condition': arm, 'episode': episode,
                             'receiving_family': family, 'chain': f'{task}-b{block}-{arm}'})
    return {'seed': seed_value, 'tasks': len(task_ids), 'chains': len(blocks)*4,
            'episodes': rows, 'status': 'allocation only; no execution or budget authorization'}


def readiness(config):
    required = ('domain_owner', 'history_manifest_sha256', 'checker_sha256', 'usefulness_rubric',
                'blinded_reviewers', 'curation_reviewer', 'budget_owner', 'spending_cap_usd',
                'labor_rate_usd_hour', 'model_settings', 'runner_version', 'external_corpus_sha256',
                'token_cap', 'tool_cap', 'verifier_cap', 'compute_cap_usd', 'wall_seconds_cap',
                'curation_minutes_cap', 'absolute_zero_baseline_threshold', 'cost_allocation',
                'isolation_evidence', 'paired_information_audit', 'retry_cases', 'estimator',
                'extension_rule', 'frozen_before_outcomes')
    missing = [name for name in required if config.get(name) in (None, '', [], {}, False)]
    return {'ready': not missing, 'missing': missing,
            'limit': 'Completeness check only. Owner must inspect actual evidence and register the protocol.'}


def cost(row, rate, amortization=1):
    """Missing cost is unknown. Never turn absent labor into a favorable zero."""
    h.require(math_is_nonnegative(rate) and type(amortization) is int and amortization > 0, 'invalid cost policy')
    amounts = [row.get('model_cost_usd'), row.get('local_compute_cost_usd')]
    labor = row.get('human_minutes', {})
    amounts += [labor.get(name) for name in LABOR_FIELDS]
    if any(x is None for x in amounts):
        return None
    h.require(all(math_is_nonnegative(x) for x in amounts), 'cost values must be finite nonnegative numbers')
    minutes = sum(labor[name] / amortization if name == 'preparation' else labor[name] for name in LABOR_FIELDS)
    return sum(amounts[:2]) + minutes * rate / 60


def math_is_nonnegative(value):
    import math
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='action', required=True)
    d = sub.add_parser('demo'); d.add_argument('destination', type=Path)
    d.add_argument('--arm', choices=list('ABCD')); d.add_argument('--tasks', type=int, choices=(1, 4), default=1)
    d.add_argument('--episodes', type=int, choices=(1, 3), default=3)
    s = sub.add_parser('schedule'); s.add_argument('config', type=Path); s.add_argument('output', type=Path)
    r = sub.add_parser('readiness'); r.add_argument('config', type=Path)
    args = p.parse_args()
    try:
        if args.action == 'demo':
            result = demo(args.destination, args.arm or 'ABCD', args.tasks, args.episodes)
        elif args.action == 'readiness':
            result = readiness(h.read_json(args.config))
        else:
            config = h.read_json(args.config)
            result = schedule(config['task_ids'], config['families'], config.get('seed', 20260905))
            h.create_file(args.output, h.encoded(result))
            result = {k: v for k, v in result.items() if k != 'episodes'}
        print(json.dumps(result, indent=2))
    except (ValueError, OSError, KeyError, subprocess.TimeoutExpired) as error:
        p.exit(1, 'Cannot complete: ' + str(error) + '\n')


if __name__ == '__main__':
    main()
