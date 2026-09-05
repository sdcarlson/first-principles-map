import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import experiment as e
import handoff as h
from fixture_checker import check


class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.store = self.root / 'store'
        self.target, self.original, self.dispute = e.seed(self.store, self.root / 'seed')

    def submission(self, name='next', edges=None, **updates):
        inbox = self.root / name; inbox.mkdir()
        if edges is None:
            edges = [[i, (i+1) % 5] for i in range(5)]
        h.create_file(inbox / 'result.json', h.encoded({'edges': edges}))
        record = e.draft(self.store, self.target, name)
        record.update(updates)
        path = inbox / 'submission.json'
        path.write_bytes(h.encoded(record))
        return path

    def accepted(self):
        attempt = h.submit(self.store, self.submission())
        receipt = h.check_attempt(self.store, attempt)
        assessment = h.assess(self.store, attempt, 'other reviewer', 'accept',
                              'Checked within finite scope.', 'No scientific value judgment.', receipt)
        return attempt, receipt, assessment

    def test_complete_path_and_original_evidence(self):
        attempt, receipt, assessment = self.accepted()
        package = self.root / 'package'
        h.export(self.store, self.target, package, 'D', e.brief(self.store, self.target))
        view = h.read_json(package / 'state.json')
        self.assertIn(assessment, view['assessments'])
        self.assertEqual(h.records(self.store, 'checks')[receipt]['status'], 'pass')
        for ref in view['attempts'][attempt]['evidence']:
            self.assertEqual((package / 'history' / ref['sha256']).read_bytes(), h.artifact(self.store, ref['sha256']))

    def test_retry_idempotent_despite_changed_snapshot(self):
        path = self.submission()
        first = h.submit(self.store, path)
        h.check_attempt(self.store, first)
        self.assertEqual(h.submit(self.store, path), first)
        candidate = path.with_name('result.json')
        candidate.write_bytes(h.encoded({'edges': []}))
        with self.assertRaisesRegex(ValueError, 'different content'):
            h.submit(self.store, path)

    def test_stale_submission_is_not_silently_rebased(self):
        stale = self.submission('stale')
        h.submit(self.store, self.submission('other'))
        with self.assertRaisesRegex(ValueError, 'stale base'):
            h.submit(self.store, stale)

    def test_no_checker_override_in_submission(self):
        path = self.submission(checker='always-pass')
        with self.assertRaisesRegex(ValueError, 'unknown fields'):
            h.submit(self.store, path)

    def test_result_cannot_override_acceptance(self):
        path = self.submission()
        path.with_name('result.json').write_bytes(h.encoded({'edges': [], 'criterion': {'degree': 0}}))
        attempt = h.submit(self.store, path)
        receipt = h.check_attempt(self.store, attempt)
        self.assertEqual(h.records(self.store, 'checks')[receipt]['status'], 'fail')

    def test_artifact_path_escape_and_absolute_path_rejected(self):
        for i, name in enumerate(('../outside.json', 'C:/file.json', 'a\\b.json')):
            path = self.submission('escape-' + str(i))
            record = h.read_json(path); record['evidence'][0]['path'] = name
            path.write_bytes(h.encoded(record))
            with self.assertRaisesRegex(ValueError, 'unsafe artifact path'):
                h.submit(self.store, path)

    def test_changed_record_is_detected(self):
        path = self.store / 'attempts' / (self.original + '.json')
        record = h.read_json(path); record['interpretation'] = 'Everything is impossible.'
        path.write_bytes(h.encoded(record))
        with self.assertRaisesRegex(ValueError, 'record digest mismatch'):
            h.snapshot(self.store)

    def test_changed_evidence_is_detected(self):
        record = h.records(self.store, 'attempts')[self.original]
        path = self.store / 'artifacts' / record['evidence'][0]['sha256']
        path.write_text('changed')
        with self.assertRaisesRegex(ValueError, 'artifact digest mismatch'):
            h.snapshot(self.store)

    def test_checker_change_fails_closed(self):
        fake = self.root / 'checker.py'; fake.write_text('print("pass")')
        with patch.object(h, 'CHECKER', fake):
            with self.assertRaisesRegex(ValueError, 'checker pin mismatch'):
                h.check_attempt(self.store, self.original)

    def test_incomplete_execution_does_not_accept_even_valid_output(self):
        attempt = h.submit(self.store, self.submission(outcome='incomplete'))
        receipt = h.check_attempt(self.store, attempt)
        with self.assertRaisesRegex(ValueError, 'incomplete execution'):
            h.assess(self.store, attempt, 'reviewer', 'accept', 'r', 'l', receipt)

    def test_incomplete_failure_remains_retryable(self):
        path = self.submission(retry_reason='The original execution was incomplete; add the missing edge.')
        attempt = h.submit(self.store, path)
        receipt = h.check_attempt(self.store, attempt)
        h.assess(self.store, attempt, 'reviewer', 'accept', 'r', 'Only this fixture.', receipt)
        self.assertEqual(h.records(self.store, 'assessments')[self.dispute]['status'], 'withhold')

    def test_acceptance_requires_independent_actor_and_correct_receipt(self):
        attempt = h.submit(self.store, self.submission())
        receipt = h.check_attempt(self.store, attempt)
        with self.assertRaisesRegex(ValueError, 'own attempt'):
            h.assess(self.store, attempt, 'fixture-worker', 'accept', 'r', 'l', receipt)
        other_receipt = h.check_attempt(self.store, self.original)
        with self.assertRaisesRegex(ValueError, 'does not match'):
            h.assess(self.store, attempt, 'reviewer', 'accept', 'r', 'l', other_receipt)
        with self.assertRaisesRegex(ValueError, 'passing independent check'):
            h.assess(self.store, attempt, 'reviewer', 'accept', 'r', 'l')

    def test_disputed_dependency_blocks_downstream_acceptance(self):
        attempt, receipt, assessment = self.accepted()
        child = h.submit(self.store, self.submission('child', depends_on=[assessment]))
        child_receipt = h.check_attempt(self.store, child)
        h.assess(self.store, attempt, 'challenger', 'challenge', 'Reconsider the claimed scope.', 'Disputed, not resolved.')
        with self.assertRaisesRegex(ValueError, 're-review'):
            h.assess(self.store, child, 'reviewer', 'accept', 'r', 'l', child_receipt)
        view = h.inspect_target(self.store, self.target, [child])
        self.assertIn(attempt, view['attempts'])
        self.assertIn(assessment, view['re_review'])
        self.assertIn('challenge', [a['status'] for a in view['assessments'].values()])

    def test_post_acceptance_challenge_marks_dependents_for_rereview(self):
        attempt, _, assessment = self.accepted()
        child = h.submit(self.store, self.submission('child', depends_on=[assessment]))
        receipt = h.check_attempt(self.store, child)
        child_assessment = h.assess(self.store, child, 'reviewer', 'accept', 'r', 'l', receipt)
        h.assess(self.store, attempt, 'challenger', 'narrow', 'Scope is narrower.', 'Review needed.')
        self.assertIn(child_assessment, h.inspect_target(self.store, self.target)['re_review'])

    def test_selected_scope_cannot_include_unrelated_target(self):
        second = h.add_target(self.store, e.fixture_target(6))
        with self.assertRaisesRegex(ValueError, 'outside target scope'):
            h.inspect_target(self.store, second, [self.original])

    def test_all_assessments_survive_export(self):
        attempt, _, assessment = self.accepted()
        newer = h.assess(self.store, attempt, 'reviewer2', 'supersede', 'Withdraw acceptance.', 'Needs more review.', supersedes=assessment)
        view = h.inspect_target(self.store, self.target, [attempt])
        self.assertIn(assessment, view['assessments']); self.assertIn(newer, view['assessments'])
        self.assertIn(assessment, view['re_review'])

    def test_four_arms_have_equal_targets_and_history_when_permitted(self):
        brief = e.brief(self.store, self.target)
        outputs = {arm: h.export(self.store, self.target, self.root / arm, arm, brief) for arm in 'ABCD'}
        self.assertEqual(outputs['C']['curated_information_sha256'], outputs['D']['curated_information_sha256'])
        self.assertEqual(len({(self.root / arm / 'target.json').read_bytes() for arm in 'ABCD'}), 1)
        self.assertFalse((self.root / 'A' / 'history').exists())
        for arm in 'BCD':
            self.assertEqual({p.name for p in (self.root / arm / 'history').iterdir()},
                             {p.name for p in (self.root / 'B' / 'history').iterdir()})
        note = (self.root / 'C' / 'handoff.md').read_text(encoding='utf-8')
        for content in brief.values(): self.assertIn(content, note)
        self.assertFalse((self.root / 'B' / 'handoff.md').exists())
        self.assertFalse((self.root / 'C' / 'state.json').exists())

    def test_raw_retrieval_finds_original_failure_and_allows_full_inventory(self):
        package = self.root / 'package'
        h.export(self.store, self.target, package, 'B', e.brief(self.store, self.target))
        self.assertTrue(any('incomplete' in x['text'] or 'closing' in x['text'] for x in h.retrieve(package, 'closing')))
        self.assertEqual(len(h.retrieve(package, '')), 4)
        self.assertEqual(h.retrieve(package, 'nonexistentword'), [])

    def test_duplicate_json_keys_and_nan_are_rejected(self):
        p = self.root / 'bad.json'
        for value in ('{"x": 1, "x": 2}', '{"x": NaN}'):
            p.write_text(value)
            with self.assertRaises(ValueError): h.read_json(p)

    def test_oversized_evidence_and_missing_scope_rejected(self):
        path = self.submission(scope='')
        with self.assertRaisesRegex(ValueError, 'scope needs text'):
            h.submit(self.store, path)
        path = self.submission('large')
        path.with_name('result.json').write_bytes(b'x' * (h.MAX_BYTES + 1))
        with self.assertRaisesRegex(ValueError, 'exceeds'):
            h.submit(self.store, path)

    def test_checker_rejects_duplicate_boolean_and_triangle_edges(self):
        c = {'n': 5, 'degree': 2, 'triangle_free': True}
        self.assertFalse(check(c, {'edges': [[True, 1]]})[0])
        self.assertFalse(check(c, {'edges': [[0, 1], [1, 0]]})[0])
        self.assertFalse(check({'n': 3, 'degree': 2, 'triangle_free': True}, {'edges': [[0, 1], [1, 2], [2, 0]]})[0])

    def test_native_inputs_equal_even_for_fresh_arm(self):
        raw = b'original current data, not internal history'
        key = h.digest(raw); h.create_file(self.store / 'artifacts' / key, raw)
        target = e.fixture_target(); target['inputs']['files'] = {'data.txt': key}
        target_key = h.add_target(self.store, target)
        for arm in 'ABCD':
            h.export(self.store, target_key, self.root / arm, arm, e.brief(self.store, target_key))
            self.assertEqual((self.root / arm / 'inputs/data.txt').read_bytes(), raw)

    def test_external_target_never_uses_fixture_checker(self):
        target = e.fixture_target()
        target['acceptance'] = {'checker': 'external-review-pending', 'checker_sha256': None,
                                'criterion': 'Independent domain-specific review required.'}
        target_key = h.add_target(self.store, target)
        attempt = h.submit(self.store, self.submission(target=target_key))
        with self.assertRaisesRegex(ValueError, 'external checker not registered'):
            h.check_attempt(self.store, attempt)

    def test_fixture_export_keeps_fixture_resource_defaults(self):
        brief = e.brief(self.store, self.target)
        info = h.export(self.store, self.target, self.root / 'fixture-resources', 'A', brief)
        self.assertEqual(info['resources'], {
            'model': 'external runner must pin', 'external_search': 'frozen corpus only',
            'fixture_wall_seconds': 5, 'fixture_model_tokens': 0})
        self.assertIn('Stop at resource caps.', info['instructions'])

    def test_external_export_leaves_caps_unassigned_and_equal_across_arms(self):
        target = e.fixture_target()
        target['acceptance'] = {'checker': 'external-review-pending', 'checker_sha256': None,
                                'criterion': 'Independent domain-specific review required.'}
        target_key = h.add_target(self.store, target)
        brief = {'current_assessment': 'Withheld.', 'unresolved_checks': 'Needs review.',
                 'proposed_next_check': 'Read the evidence.'}
        outputs = {arm: h.export(self.store, target_key, self.root / ('ext-' + arm), arm, brief)
                   for arm in 'ABCD'}
        resources = [outputs[arm]['resources'] for arm in 'ABCD']
        self.assertEqual(resources[0], resources[1])
        self.assertEqual(resources[0], resources[2])
        self.assertEqual(resources[0], resources[3])
        r = resources[0]
        self.assertIsNone(r['model'])
        self.assertIsNone(r['compute'])
        self.assertNotIn('fixture_model_tokens', r)
        self.assertNotIn('fixture_wall_seconds', r)
        self.assertIn('owner-assigned', r['limits'])
        for arm in 'ABCD':
            self.assertEqual(outputs[arm]['resources'], r)
            self.assertIn('not an authorized full scientific run', outputs[arm]['instructions'])
            self.assertIn("cannot change the checker's pinned acceptance", outputs[arm]['instructions'])
            self.assertNotIn('Stop at resource caps.', outputs[arm]['instructions'])


class ExperimentTests(unittest.TestCase):
    def test_schedule_matches_orders_across_arms_and_balances_families(self):
        plan = e.schedule([f't{i}' for i in range(12)], ['f1', 'f2', 'f3'])
        self.assertEqual(plan['chains'], 96); self.assertEqual(len(plan['episodes']), 288)
        orders = {}
        for row in plan['episodes']:
            key = (row['task'], row['block'], row['condition'])
            orders.setdefault(key, []).append(row['receiving_family'])
        for task in [f't{i}' for i in range(12)]:
            for block in (1, 2):
                self.assertEqual(len({tuple(orders[(task, block, arm)]) for arm in 'ABCD'}), 1)
        from collections import Counter
        self.assertEqual(set(Counter(tuple(v) for k, v in orders.items() if k[2] == 'A').values()), {4})

    def test_missing_costs_never_become_zero(self):
        self.assertIsNone(e.cost({}, 100))
        row = {'model_cost_usd': 2, 'local_compute_cost_usd': 1,
               'human_minutes': {x: 6 for x in e.LABOR_FIELDS}}
        self.assertEqual(e.cost(row, 60), 33)
        self.assertEqual(e.cost(row, 60, 5), 28.2)
        row['human_minutes']['review'] = -1
        with self.assertRaises(ValueError): e.cost(row, 60)

    def test_research_readiness_lists_exact_missing_dependencies(self):
        result = e.readiness({})
        self.assertFalse(result['ready'])
        self.assertIn('history_manifest_sha256', result['missing'])
        self.assertIn('spending_cap_usd', result['missing'])

    def test_full_four_arm_fresh_process_chain(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / 'demo'
            result = e.demo(dest)
            self.assertEqual(result['checked_episodes'], 12)
            self.assertFalse(result['research_experiment_run'])
            ledger = h.read_json(dest / 'ledger.json')
            self.assertTrue(all(row['metrics']['useful_progress_units'] is None for row in ledger))
            a = json.loads((dest / 'task-1/A/episode-3/output/worker-output.json').read_text())
            b = json.loads((dest / 'task-1/B/episode-3/output/worker-output.json').read_text())
            self.assertFalse(any(x.startswith('history/') for x in a['observed_files']))
            self.assertTrue(any(x.startswith('history/') for x in b['observed_files']))
            initial = [h.read_json(dest / f'task-1/{arm}/episode-1/input/assignment.json') for arm in 'CD']
            self.assertEqual(initial[0]['curated_information_sha256'], initial[1]['curated_information_sha256'])


if __name__ == '__main__':
    unittest.main()
