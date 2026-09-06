import json
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from unittest.mock import patch
from urllib.parse import unquote, urlparse

import experiment as e
import handoff as h
import start
import release


class HrefParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for key, value in attrs:
                if key == 'href' and value is not None:
                    self.hrefs.append(value)


HERE = Path(__file__).resolve().parent
PHYSICS = HERE / 'physics'
DEFAULT_STORE = PHYSICS / 'store'


def file_inventory(root):
    return {p.relative_to(root).as_posix(): h.digest(p.read_bytes())
            for p in sorted(root.rglob('*')) if p.is_file()}


def copy_public_store(dest):
    dest = Path(dest)
    for rel in release.PUBLIC_STORE_FILES:
        src = DEFAULT_STORE / rel
        out = dest / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(src.read_bytes())
    return dest


def make_dir_redirect(target, link):
    target = os.path.abspath(target)
    link = Path(link)
    try:
        os.symlink(target, link, target_is_directory=True)
        return True
    except OSError:
        pass
    if os.name == 'nt':
        done = subprocess.run(['cmd', '/c', 'mklink', '/J', str(link), target],
                              capture_output=True, text=True)
        return done.returncode == 0
    return False


def mechanics_submission(store, inbox, request_id, observation, snapshot=None):
    inbox = Path(inbox)
    inbox.mkdir(parents=True, exist_ok=True)
    payload = b'SOFTWARE-MECHANICS synthetic bytes. Not research evidence.\n'
    h.create_file(inbox / 'result.json', payload)
    record = {
        'request_id': request_id,
        'base_snapshot': snapshot if snapshot is not None else h.snapshot(store),
        'target': start.DEFAULT_TARGET,
        'method': 'SOFTWARE-MECHANICS synthetic import test. Not research evidence.',
        'scope': h.records(store, 'targets')[start.DEFAULT_TARGET]['scope'],
        'inputs': {},
        'environment': 'unittest temporary directory',
        'budget': {'human_minutes': None, 'compute_usd': None},
        'outcome': 'completed',
        'observation': observation,
        'interpretation': 'Toolkit import test only; not a physics result.',
        'retry_reason': 'SOFTWARE-MECHANICS synthetic return. Not research evidence.',
        'depends_on': [],
        'provenance': {
            'contributor': 'software-mechanics-test',
            'model': 'none',
            'configuration': 'unittest',
            'source_locator': 'test_release.py',
            'shared_roots': 'SOFTWARE-MECHANICS only; not research evidence.',
        },
        'evidence': [{'path': 'result.json', 'role': 'result',
                      'source': 'SOFTWARE-MECHANICS synthetic fixture-shaped JSON',
                      'locator': 'entire file'}],
    }
    path = inbox / 'submission.json'
    path.write_bytes(h.encoded(record))
    return path


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_validate_reference_store_accepts_default_and_rejects_unrelated(self):
        release.validate_reference_store(DEFAULT_STORE, start.DEFAULT_TARGET)
        self.assertEqual(h.snapshot(DEFAULT_STORE), release.FROZEN_SNAPSHOT)
        store = self.root / 'store'
        e.seed(store, self.root / 'seed')
        with self.assertRaisesRegex(ValueError, 'unexpected|exact|snapshot|not the public|allowlist'):
            release.validate_reference_store(store, start.DEFAULT_TARGET)
        h.add_target(store, e.fixture_target(6))
        with self.assertRaisesRegex(ValueError, 'exactly one target|unexpected|exact|snapshot|allowlist'):
            release.validate_reference_store(store, start.DEFAULT_TARGET)

    def test_build_packages_default_example_with_manifest_zip_and_toolkit(self):
        dest, zipped = release.build(self.root / 'pkg')
        self.assertEqual(dest, self.root / 'pkg')
        self.assertEqual(zipped, self.root / 'pkg.zip')
        self.assertTrue((dest / 'index.html').is_file())
        self.assertTrue((dest / 'START.md').is_file())
        self.assertTrue((dest / 'USE.md').is_file())
        self.assertTrue((dest / 'submission-template.json').is_file())
        self.assertTrue((dest / 'toolkit' / 'handoff.py').is_file())
        self.assertTrue((dest / 'toolkit' / 'fixture_checker.py').is_file())
        self.assertEqual((dest / 'toolkit' / 'handoff.py').read_bytes(), (HERE / 'handoff.py').read_bytes())
        self.assertEqual((dest / 'toolkit' / 'fixture_checker.py').read_bytes(),
                         (HERE / 'fixture_checker.py').read_bytes())
        assignment = h.read_json(dest / 'C' / 'assignment.json')
        self.assertEqual(h.snapshot(dest / 'store'), assignment['base_snapshot'])
        self.assertEqual(assignment['target'], start.DEFAULT_TARGET)
        self.assertEqual(assignment['base_snapshot'], release.FROZEN_SNAPSHOT)
        self.assertEqual(h.snapshot(dest / 'store'), h.snapshot(DEFAULT_STORE))
        store_files = {p.relative_to(dest / 'store').as_posix()
                       for p in (dest / 'store').rglob('*') if p.is_file()}
        self.assertEqual(store_files, set(release.PUBLIC_STORE_FILES))
        for rel in release.PUBLIC_STORE_FILES:
            self.assertEqual((dest / 'store' / rel).read_bytes(), (DEFAULT_STORE / rel).read_bytes())
        source = PHYSICS / 'store' / 'artifacts' / (
            'f948c9be21949f84e1679ab380dde6553183782bdc46f4be8c7a8845da732a68')
        self.assertEqual((dest / 'C' / 'inputs' / 'switching.py').read_bytes(), source.read_bytes())
        licenses = list(dest.rglob('upstream-license.txt'))
        self.assertTrue(licenses)
        self.assertTrue(any(b'BSD 3-Clause' in p.read_bytes() for p in licenses))
        self.assertFalse((dest / 'LICENSE').exists())
        self.assertFalse((dest / 'start.py').exists())
        self.assertFalse((dest / 'vacuum_baseline.py').exists())
        self.assertFalse((dest / 'DECISION.md').exists())
        manifest = h.read_json(dest / 'manifest.json')
        self.assertEqual(list(manifest), sorted(manifest))
        self.assertNotIn('manifest.json', manifest)
        on_disk = file_inventory(dest)
        self.assertEqual(manifest, {k: v for k, v in on_disk.items() if k != 'manifest.json'})
        html = (dest / 'index.html').read_text(encoding='utf-8')
        parser = HrefParser()
        parser.feed(html)
        self.assertTrue(parser.hrefs)
        for href in parser.hrefs:
            path = unquote(urlparse(href).path)
            self.assertTrue((dest.joinpath(*path.split('/'))).is_file(), href)
        template = h.read_json(dest / 'submission-template.json')
        fenced = (dest / 'START.md').read_text(encoding='utf-8')
        self.assertEqual(template, json.loads(fenced.split('Valid submission template:\n', 1)[1].rsplit('\n```', 1)[0]))
        self.assertIn('python toolkit/handoff.py --store store submit', (dest / 'USE.md').read_text(encoding='utf-8'))
        use = (dest / 'USE.md').read_text(encoding='utf-8')
        html = (dest / 'index.html').read_text(encoding='utf-8')
        md = (dest / 'START.md').read_text(encoding='utf-8')
        for text in (use, html, md):
            self.assertIn('python toolkit/handoff.py --store store submit', text)
            self.assertIn('python toolkit/handoff.py --store store inspect', text)
            self.assertIn('python toolkit/handoff.py --store store check ATTEMPT', text)
            self.assertIn('python toolkit/handoff.py --store store assess ATTEMPT --reviewer REVIEWER --status withhold', text)
            self.assertNotIn('PATH_TO_OWNER_STORE', text)
        self.assertIn('public-reference demonstration', use)
        self.assertIn('WHOLE folder', html)
        self.assertIn(start.DEFAULT_TARGET, (dest / 'USE.md').read_text(encoding='utf-8'))
        self.assertIn(assignment['base_snapshot'], (dest / 'USE.md').read_text(encoding='utf-8'))

    def test_repeated_builds_are_byte_identical_and_collision_refuses(self):
        first, zip_a = release.build(self.root / 'a')
        second, zip_b = release.build(self.root / 'b')
        self.assertEqual(file_inventory(first), file_inventory(second))
        self.assertEqual(zip_a.read_bytes(), zip_b.read_bytes())
        with zipfile.ZipFile(zip_a) as zf:
            for info in zf.infolist():
                self.assertEqual(info.date_time, (1980, 1, 1, 0, 0, 0))
                self.assertNotIn('\\', info.filename)
                self.assertFalse(info.filename.startswith('/'))
                self.assertNotIn('..', info.filename.split('/'))
            names = zf.namelist()
            self.assertEqual(names, sorted(names))
            self.assertEqual(set(names), set(file_inventory(first)))
        use_before = (first / 'USE.md').read_bytes()
        zip_before = zip_a.read_bytes()
        with self.assertRaisesRegex(ValueError, 'overwrite|already exists'):
            release.build(self.root / 'a')
        self.assertEqual((first / 'USE.md').read_bytes(), use_before)
        self.assertEqual(zip_a.read_bytes(), zip_before)
        zip_only = self.root / 'c.zip'
        zip_only.write_bytes(b'existing-zip')
        with self.assertRaisesRegex(ValueError, 'overwrite|already exists'):
            release.build(self.root / 'c')
        self.assertEqual(zip_only.read_bytes(), b'existing-zip')
        self.assertFalse((self.root / 'c').exists())

    def test_package_has_no_private_or_runtime_paths(self):
        dest, zipped = release.build(self.root / 'scan')
        forbidden = ('vacuum_baseline.py', 'DECISION.md', 'runtime.json', 'release-implementation.txt',
                     'usability-audit.md', 'release-audit.md')
        temp_s = str(self.root)
        for p in dest.rglob('*'):
            if not p.is_file():
                continue
            rel = p.relative_to(dest).as_posix()
            self.assertNotIn('__pycache__', rel.split('/'))
            self.assertFalse(rel.endswith('.pyc'))
            self.assertNotIn('evidence/local', rel)
            self.assertNotIn('research/vacuum', rel)
            self.assertNotIn(p.name, forbidden)
            raw = p.read_bytes()
            self.assertNotIn(temp_s.encode('utf-8'), raw)
            self.assertNotIn(b'C:\\Users\\', raw)
            self.assertNotIn(b'/Users/', raw)
        with zipfile.ZipFile(zipped) as zf:
            self.assertNotIn('LICENSE', zf.namelist())
            self.assertTrue(any(name.endswith('upstream-license.txt') for name in zf.namelist()))

    def test_extracted_zip_cli_imports_software_mechanics_and_withholds(self):
        dest, zipped = release.build(self.root / 'boxed')
        extracted = self.root / 'extracted'
        extracted.mkdir()
        with zipfile.ZipFile(zipped) as zf:
            zf.extractall(extracted)
        self.assertEqual(file_inventory(extracted), file_inventory(dest))
        assignment = h.read_json(extracted / 'C' / 'assignment.json')
        self.assertEqual(assignment['base_snapshot'], release.FROZEN_SNAPSHOT)
        self.assertEqual(h.snapshot(extracted / 'store'), release.FROZEN_SNAPSHOT)
        for arm in 'ABCD':
            arm_asg = h.read_json(extracted / arm / 'assignment.json')
            self.assertEqual(arm_asg['base_snapshot'], release.FROZEN_SNAPSHOT)
            self.assertEqual(arm_asg['target'], start.DEFAULT_TARGET)
        self.assertEqual(h.read_json(extracted / 'D' / 'assignment.json')['curated_information_sha256'],
                         h.read_json(extracted / 'C' / 'assignment.json')['curated_information_sha256'])
        self.assertEqual(h.read_json(extracted / 'submission-template.json')['base_snapshot'],
                         release.FROZEN_SNAPSHOT)
        target = assignment['target']
        cli = [sys.executable, str(extracted / 'toolkit' / 'handoff.py'),
               '--store', str(extracted / 'store')]
        inspect = subprocess.run(cli + ['inspect', target], capture_output=True, text=True, cwd=extracted)
        self.assertEqual(inspect.returncode, 0, inspect.stderr)
        view = json.loads(inspect.stdout)
        self.assertEqual(view['target'], target)
        self.assertEqual(set(view['targets']), {target})
        inbox = self.root / 'return-folder'
        inbox.mkdir()
        fixture_result = {'edges': [[i, (i + 1) % 5] for i in range(5)]}
        h.create_file(inbox / 'result.json', h.encoded(fixture_result))
        checker_bytes = (extracted / 'toolkit' / 'fixture_checker.py').read_bytes()
        h.create_file(inbox / 'fixture_checker.py', checker_bytes)
        submission = h.read_json(extracted / 'submission-template.json')
        submission['request_id'] = 'software-mechanics-synthetic-1'
        submission['method'] = 'SOFTWARE-MECHANICS synthetic import test. Not research evidence.'
        submission['observation'] = 'SOFTWARE-MECHANICS synthetic returned attempt. Not research evidence.'
        submission['interpretation'] = 'Toolkit import test only; not a physics result.'
        submission['environment'] = 'unittest temporary directory'
        submission['provenance'] = {
            'contributor': 'software-mechanics-test',
            'model': 'none',
            'configuration': 'unittest',
            'source_locator': 'test_release.py',
            'shared_roots': 'SOFTWARE-MECHANICS only; not research evidence.',
        }
        submission['evidence'] = [
            {'path': 'result.json', 'role': 'result',
             'source': 'SOFTWARE-MECHANICS synthetic fixture-shaped JSON', 'locator': 'entire file'},
            {'path': 'fixture_checker.py', 'role': 'source',
             'source': 'original packaged fixture_checker.py bytes', 'locator': 'entire file'},
        ]
        h.create_file(inbox / 'submission.json', h.encoded(submission))
        imported = subprocess.run(cli + ['submit', str(inbox / 'submission.json')],
                                  capture_output=True, text=True, cwd=extracted)
        self.assertEqual(imported.returncode, 0, imported.stderr)
        attempt = json.loads(imported.stdout)
        self.assertEqual((extracted / 'store' / 'artifacts' / h.digest(checker_bytes)).read_bytes(),
                         checker_bytes)
        checked = subprocess.run(cli + ['check', attempt], capture_output=True, text=True, cwd=extracted)
        self.assertNotEqual(checked.returncode, 0)
        self.assertIn('external checker not registered', checked.stderr)
        withheld = subprocess.run(
            cli + ['assess', attempt, '--reviewer', 'release-test-reviewer', '--status', 'withhold',
                   '--rationale', 'SOFTWARE-MECHANICS import test; physics checker unavailable.',
                   '--limitations', 'Not research evidence.'],
            capture_output=True, text=True, cwd=extracted)
        self.assertEqual(withheld.returncode, 0, withheld.stderr)
        assessment = json.loads(withheld.stdout)
        record = h.records(extracted / 'store', 'assessments')[assessment]
        self.assertEqual(record['status'], 'withhold')
        self.assertEqual(record['attempt'], attempt)
        self.assertFalse(record['useful'])
        self.assertIn('not authenticated', record['identity_limit'].lower())
        extra = subprocess.run(cli + ['check', attempt], capture_output=True, text=True, cwd=extracted)
        self.assertNotEqual(extra.returncode, 0)
        retry = subprocess.run(cli + ['submit', str(inbox / 'submission.json')],
                               capture_output=True, text=True, cwd=extracted)
        self.assertEqual(retry.returncode, 0, retry.stderr)
        self.assertEqual(json.loads(retry.stdout), attempt)
        changed = h.read_json(inbox / 'submission.json')
        changed['observation'] = 'SOFTWARE-MECHANICS changed same request id. Not research evidence.'
        (inbox / 'submission.json').write_bytes(h.encoded(changed))
        collided = subprocess.run(cli + ['submit', str(inbox / 'submission.json')],
                                  capture_output=True, text=True, cwd=extracted)
        self.assertNotEqual(collided.returncode, 0)
        self.assertIn('different content', collided.stderr)
        stale_inbox = self.root / 'stale-return'
        stale_path = mechanics_submission(
            extracted / 'store', stale_inbox, 'software-mechanics-stale-2',
            'SOFTWARE-MECHANICS stale snapshot return. Not research evidence.',
            snapshot=assignment['base_snapshot'])
        stale = subprocess.run(cli + ['submit', str(stale_path)],
                               capture_output=True, text=True, cwd=extracted)
        self.assertNotEqual(stale.returncode, 0)
        self.assertIn('stale', stale.stderr.lower())
        accepted = subprocess.run(
            cli + ['assess', attempt, '--reviewer', 'other-release-reviewer', '--status', 'accept',
                   '--rationale', 'SOFTWARE-MECHANICS must not accept without a passing physics check.',
                   '--limitations', 'Not research evidence.'],
            capture_output=True, text=True, cwd=extracted)
        self.assertNotEqual(accepted.returncode, 0)
        self.assertIn('passing independent check', accepted.stderr)

    def test_same_target_private_attempt_is_rejected_with_no_output(self):
        store = copy_public_store(self.root / 'extra-attempt-store')
        mechanics_submission(store, self.root / 'extra-inbox', 'software-mechanics-extra-same-target',
                             'SOFTWARE-MECHANICS extra same-target attempt. Not research evidence.')
        h.submit(store, self.root / 'extra-inbox' / 'submission.json')
        dest = self.root / 'should-not-exist'
        with patch.object(start, 'DEFAULT_STORE', store):
            with self.assertRaisesRegex(ValueError, 'unexpected|exact|snapshot|allowlist'):
                release.build(dest)
        self.assertFalse(dest.exists())
        self.assertFalse((self.root / 'should-not-exist.zip').exists())

    def test_unused_files_in_artifacts_and_records_are_rejected_with_no_output(self):
        for kind, name in (('artifacts', 'unreferenced-note.txt'),
                           ('attempts', 'unreferenced-note.txt')):
            store = copy_public_store(self.root / ('unused-' + kind))
            (store / kind / name).write_text('SOFTWARE-MECHANICS PRIVATE_SENTINEL', encoding='utf-8')
            dest = self.root / ('out-' + kind)
            with patch.object(start, 'DEFAULT_STORE', store):
                with self.assertRaisesRegex(ValueError, 'unexpected|exact|allowlist'):
                    release.build(dest)
            self.assertFalse(dest.exists())
            self.assertFalse(dest.with_name(dest.name + '.zip').exists())

    def test_redirected_source_is_rejected_before_export(self):
        real = copy_public_store(self.root / 'real-store')
        link = self.root / 'linked-store'
        self.assertTrue(make_dir_redirect(real, link), msg='could not create a directory redirect for the test')
        dest = self.root / 'from-redirect'
        with patch.object(start, 'DEFAULT_STORE', link):
            with self.assertRaisesRegex(ValueError, 'redirect|symlink|junction|reparse'):
                release.build(dest)
        self.assertFalse(dest.exists())
        self.assertFalse((self.root / 'from-redirect.zip').exists())

    def test_nested_redirected_directory_is_rejected_with_no_output(self):
        store = copy_public_store(self.root / 'nested-link-store')
        hidden = self.root / 'hidden-nested'
        hidden.mkdir()
        (hidden / 'secret.txt').write_text('SOFTWARE-MECHANICS PRIVATE_SENTINEL', encoding='utf-8')
        link = store / 'artifacts' / 'nested'
        self.assertTrue(make_dir_redirect(hidden, link),
                        msg='could not create a nested directory redirect for the test')
        dest = self.root / 'nested-link-out'
        with patch.object(start, 'DEFAULT_STORE', store):
            with self.assertRaisesRegex(ValueError, 'redirect|symlink|junction|reparse|unexpected nested'):
                release.build(dest)
        self.assertFalse(dest.exists())
        self.assertFalse((self.root / 'nested-link-out.zip').exists())

    def test_nested_empty_directory_is_rejected_with_no_output(self):
        store = copy_public_store(self.root / 'nested-empty-store')
        (store / 'artifacts' / 'empty-dir').mkdir()
        dest = self.root / 'nested-empty-out'
        with patch.object(start, 'DEFAULT_STORE', store):
            with self.assertRaisesRegex(ValueError, 'unexpected nested|empty store|non-file'):
                release.build(dest)
        self.assertFalse(dest.exists())
        self.assertFalse((self.root / 'nested-empty-out.zip').exists())

    def test_redirected_brief_is_rejected_with_no_output(self):
        physics = start.MVP_BRIEF.parent
        link_root = self.root / 'brief-junction'
        self.assertTrue(make_dir_redirect(physics, link_root),
                        msg='could not create a brief parent redirect for the test')
        dest = self.root / 'brief-link-out'
        with patch.object(start, 'MVP_BRIEF', link_root / start.MVP_BRIEF.name):
            with self.assertRaisesRegex(ValueError, 'redirect|symlink|junction|reparse'):
                release.build(dest)
        self.assertFalse(dest.exists())
        self.assertFalse((self.root / 'brief-link-out.zip').exists())

    def test_redirected_toolkit_is_rejected_with_no_output(self):
        link_here = self.root / 'here-junction'
        self.assertTrue(make_dir_redirect(HERE, link_here),
                        msg='could not create a toolkit parent redirect for the test')
        dest = self.root / 'toolkit-link-out'
        with patch.object(release, 'HERE', link_here):
            with self.assertRaisesRegex(ValueError, 'redirect|symlink|junction|reparse'):
                release.build(dest)
        self.assertFalse(dest.exists())
        self.assertFalse((self.root / 'toolkit-link-out.zip').exists())

    def test_cli_runs_from_another_working_directory(self):
        dest = self.root / 'elsewhere' / 'out'
        done = subprocess.run(
            [sys.executable, str(HERE / 'release.py'), str(dest)],
            capture_output=True, text=True, cwd=self.root)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertTrue((dest / 'manifest.json').is_file())
        self.assertTrue((dest.parent / 'out.zip').is_file())


if __name__ == '__main__':
    unittest.main()
