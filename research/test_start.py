from html.parser import HTMLParser
import html as html_lib
import json
import re
import tempfile
import unittest
from pathlib import Path
from urllib.parse import unquote, urlparse

import experiment as e
import handoff as h
import start


class HrefParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for key, value in attrs:
                if key == 'href' and value is not None:
                    self.hrefs.append(value)


def extract_fenced_prompt(md):
    _, _, rest = md.partition('## Recipient prompt')
    match = re.search(r'^(`{3,})\n', rest, re.M)
    ticks = match.group(1)
    body = rest[match.end():]
    closer = '\n' + ticks + '\n'
    idx = body.find(closer)
    if idx == -1:
        idx = body.rfind('\n' + ticks)
    return body[:idx]


def markdown_prose(md):
    pieces = []
    i = 0
    while True:
        match = re.search(r'^(`{3,})\n', md[i:], re.M)
        if not match:
            pieces.append(md[i:])
            return ''.join(pieces)
        ticks = match.group(1)
        pieces.append(md[i:i + match.start()])
        body_start = i + match.end()
        closer = '\n' + ticks + '\n'
        idx = md.find(closer, body_start)
        if idx == -1:
            idx = md.find('\n' + ticks, body_start)
            return ''.join(pieces)
        i = idx + len(closer)


HERE = Path(__file__).resolve().parent
PHYSICS = HERE / 'physics'


class StartTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_generation_writes_page_packages_and_preserves_bytes(self):
        dest = self.root / 'out'
        before = (PHYSICS / 'C' / 'assignment.json').read_bytes()
        brief_before = (PHYSICS / 'brief.json').read_bytes()
        source = (PHYSICS / 'store' / 'artifacts' /
                  'f948c9be21949f84e1679ab380dde6553183782bdc46f4be8c7a8845da732a68')
        start.build(dest)
        self.assertTrue((dest / 'index.html').is_file())
        self.assertTrue((dest / 'START.md').is_file())
        html = (dest / 'index.html').read_text(encoding='utf-8')
        md = (dest / 'START.md').read_text(encoding='utf-8')
        self.assertIn('href="C/handoff.md"', html)
        self.assertIn('href="D/state.json"', html)
        self.assertIn('href="C/inputs/switching.py"', html)
        self.assertIn('href="A/assignment.json"', html)
        self.assertIn('href="B/assignment.json"', html)
        self.assertIn('C/handoff.md', md)
        self.assertIn('D/state.json', md)
        self.assertTrue((dest / 'C' / 'handoff.md').is_file())
        self.assertTrue((dest / 'D' / 'state.json').is_file())
        self.assertEqual((dest / 'C' / 'inputs' / 'switching.py').read_bytes(), source.read_bytes())
        c = h.read_json(dest / 'C' / 'assignment.json')
        d = h.read_json(dest / 'D' / 'assignment.json')
        self.assertEqual(c['curated_information_sha256'], d['curated_information_sha256'])
        self.assertEqual(c['resources'], d['resources'])
        self.assertIsNone(c['resources']['model'])
        self.assertIsNone(c['resources']['compute'])
        self.assertNotIn('fixture_model_tokens', c['resources'])
        self.assertIn('owner-assigned', c['resources']['limits'])
        self.assertIn('not an authorized full scientific run', html)
        self.assertIn('cannot launch', html.lower())
        self.assertNotIn('<script src', html)
        self.assertNotIn('<link ', html)
        self.assertEqual((PHYSICS / 'C' / 'assignment.json').read_bytes(), before)
        self.assertIn('id="recipient-prompt"', html)
        self.assertIn('id="copy-prompt"', html)
        self.assertIn('href="START.md"', html)
        self.assertIn('for="recipient-prompt"', html)
        self.assertTrue('overflow-wrap' in html or 'word-break' in html)
        self.assertIn('remove each evidence sha256', html.lower())
        self.assertIn('exactly one result', html.lower())
        self.assertIn('stale', html.lower())
        self.assertTrue('"role": "result"' in html or '&quot;role&quot;: &quot;result&quot;' in html)
        self.assertIn('assumptions', html.lower())
        self.assertIn('stop_condition', html.lower())
        self.assertIn('finite Fourier', html)
        self.assertIn('Do not repeat the already-completed review', html)
        self.assertNotIn('Review the two analytic normalization identities against the attached numerical output without asking the previous author', html)
        self.assertEqual((PHYSICS / 'brief.json').read_bytes(), brief_before)

    def test_refuses_existing_output(self):
        dest = self.root / 'exists'
        dest.mkdir()
        (dest / 'keep.txt').write_text('do not touch', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'overwrite|already exists|must be new'):
            start.build(dest)
        self.assertEqual((dest / 'keep.txt').read_text(encoding='utf-8'), 'do not touch')
        self.assertFalse((dest / 'index.html').exists())

    def test_escapes_hostile_html_in_starting_page(self):
        store = self.root / 'store'
        raw = b'original-bytes-<script>alert(1)</script>'
        key = h.digest(raw)
        h.create_file(store / 'artifacts' / key, raw)
        target = e.fixture_target()
        target['id'] = 'hostile-html'
        target['owner'] = 'tester <b>bold</b>'
        target['question'] = 'Does <script>alert(1)</script> break the page? ![x](https://evil.example/x.png)'
        target['scope'] = 'Escape "quotes" and <img src=x onerror=alert(1)>.'
        target['acceptance'] = {'checker': 'external-review-pending', 'checker_sha256': None,
                                'criterion': 'Independent review; <svg/onload=alert(1)> is data.'}
        target['inputs'] = {'files': {'note.txt': key}}
        target_key = h.add_target(store, target)
        brief = {
            'current_assessment': 'Withheld <script>alert("brief")</script>.',
            'unresolved_checks': 'Need review of <iframe src="https://evil.example">.',
            'proposed_next_check': 'Read note.txt; do not execute <script>.'}
        dest = self.root / 'hostile'
        start.build(dest, store, target_key, brief)
        html = (dest / 'index.html').read_text(encoding='utf-8')
        self.assertNotIn('<script>alert(1)</script>', html)
        self.assertNotIn('<script>alert("brief")</script>', html)
        self.assertNotIn('<img src=x onerror=alert(1)>', html)
        self.assertNotIn('<svg/onload=alert(1)>', html)
        self.assertNotIn('<b>bold</b>', html)
        self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt;', html)
        self.assertIn('&lt;b&gt;bold&lt;/b&gt;', html)
        self.assertIn('href="C/inputs/note.txt"', html)
        self.assertEqual((dest / 'C' / 'inputs' / 'note.txt').read_bytes(), raw)
        self.assertNotIn('<script src', html)
        self.assertNotIn('src="https://evil.example"', html)
        md = (dest / 'START.md').read_text(encoding='utf-8')
        prose = markdown_prose(md)
        self.assertNotIn('<script>alert(1)</script>', prose)
        self.assertNotIn('<b>bold</b>', prose)
        self.assertNotIn('![x](https://evil.example/x.png)', prose)
        self.assertNotIn('<iframe src="https://evil.example">', prose)

    def test_start_preserves_fixture_resource_defaults(self):
        store = self.root / 'store'
        target, _, _ = e.seed(store, self.root / 'seed')
        dest = self.root / 'fixture-out'
        start.build(dest, store, target, e.brief(store, target))
        resources = [h.read_json(dest / arm / 'assignment.json')['resources'] for arm in 'ABCD']
        expected = {'model': 'external runner must pin', 'external_search': 'frozen corpus only',
                    'fixture_wall_seconds': 5, 'fixture_model_tokens': 0}
        self.assertEqual(resources[0], expected)
        self.assertEqual(resources[0], resources[1])
        self.assertEqual(resources[0], resources[2])
        self.assertEqual(resources[0], resources[3])

    def _external_target(self, store, files, **updates):
        target = e.fixture_target()
        target['id'] = 'link-encoding'
        target['acceptance'] = {'checker': 'external-review-pending', 'checker_sha256': None,
                                'criterion': 'Independent review of attached bytes.'}
        target['inputs'] = {'files': files}
        target.update(updates)
        return h.add_target(store, target)

    def test_special_input_names_encode_hrefs_and_preserve_bytes(self):
        store = self.root / 'store'
        names = {'a#b.txt': b'hash-bytes', 'a b.txt': b'space-bytes', 'a[b].txt': b'bracket-bytes',
                 'a(b).txt': b'paren-bytes', 'pct%.txt': b'percent-bytes'}
        files = {}
        for name, raw in names.items():
            key = h.digest(raw)
            h.create_file(store / 'artifacts' / key, raw)
            files[name] = key
        target_key = self._external_target(store, files)
        brief = {'current_assessment': 'Withheld.', 'unresolved_checks': 'Needs review.',
                 'proposed_next_check': 'Read the attached files.'}
        dest = self.root / 'encoded'
        start.build(dest, store, target_key, brief)
        html = (dest / 'index.html').read_text(encoding='utf-8')
        md = (dest / 'START.md').read_text(encoding='utf-8')
        parser = HrefParser()
        parser.feed(html)
        for name, raw in names.items():
            real = 'C/inputs/' + name
            self.assertIn(real, html)
            self.assertTrue((dest / 'C' / 'inputs' / name).is_file())
            self.assertEqual((dest / 'C' / 'inputs' / name).read_bytes(), raw)
            self.assertNotIn('href="' + real + '"', html)
            matches = [href for href in parser.hrefs
                       if unquote(urlparse(href).path) == real or unquote(href) == real]
            self.assertEqual(len(matches), 1, msg=name + ' hrefs=' + str(parser.hrefs))
            parsed = urlparse(matches[0])
            self.assertEqual(parsed.fragment, '')
            self.assertNotIn('#', parsed.path)
            resolved = dest.joinpath(*unquote(parsed.path).split('/'))
            self.assertEqual(resolved.read_bytes(), raw)
            self.assertIn('](' + matches[0] + ')', md)
            self.assertNotIn('](' + real + ')', md)

    def test_custom_store_without_brief_is_rejected_before_output(self):
        store = self.root / 'store'
        target_key = self._external_target(store, {})
        dest = self.root / 'custom-store-out'
        with self.assertRaisesRegex(ValueError, 'brief'):
            start.build(dest, store, target_key)
        self.assertFalse(dest.exists())
        with self.assertRaises(SystemExit) as caught:
            start.main([str(dest), '--store', str(store), '--target', target_key])
        self.assertEqual(caught.exception.code, 1)
        self.assertFalse(dest.exists())

    def test_custom_target_without_brief_is_rejected_before_output(self):
        dest = self.root / 'custom-target-out'
        with self.assertRaisesRegex(ValueError, 'brief'):
            start.build(dest, target='not-the-default-target')
        self.assertFalse(dest.exists())
        with self.assertRaises(SystemExit) as caught:
            start.main([str(dest), '--target', 'not-the-default-target'])
        self.assertEqual(caught.exception.code, 1)
        self.assertFalse(dest.exists())

    def test_fenced_prompt_bytes_match_recipient_and_decoded_textarea(self):
        store = self.root / 'store'
        raw = b'bytes'
        key = h.digest(raw)
        h.create_file(store / 'artifacts' / key, raw)
        target = e.fixture_target()
        target['id'] = 'copy-bytes'
        target['owner'] = 'tester <b>bold</b>'
        target['question'] = 'See ```json and <script>alert(1)</script>'
        target['scope'] = 'Keep original prompt bytes, including backticks.'
        target['acceptance'] = {'checker': 'external-review-pending', 'checker_sha256': None,
                                'criterion': 'Independent review; quotes "must" survive copy.'}
        target['inputs'] = {'files': {'note.txt': key}}
        target_key = h.add_target(store, target)
        brief = {
            'current_assessment': 'Withheld <script>alert("brief")</script>.',
            'unresolved_checks': 'Need review of <iframe src="https://evil.example">.',
            'proposed_next_check': 'Copy the template; do not execute ``` or <script>.'}
        dest = self.root / 'copy-bytes'
        start.build(dest, store, target_key, brief)
        assignment = h.read_json(dest / 'C' / 'assignment.json')
        view = h.inspect_target(store, target_key)
        expected = start.recipient_prompt(target_key, view['targets'][target_key], brief, view, assignment)
        md = (dest / 'START.md').read_text(encoding='utf-8')
        html_page = (dest / 'index.html').read_text(encoding='utf-8')
        fenced = extract_fenced_prompt(md)
        self.assertEqual(fenced, expected)
        textarea = re.search(r'<textarea id="recipient-prompt"[^>]*>(.*?)</textarea>', html_page, re.S)
        self.assertEqual(html_lib.unescape(textarea.group(1)), expected)
        self.assertIn('```json', fenced)
        self.assertIn('<script>alert(1)</script>', fenced)
        template = json.loads(fenced.split('Valid submission template:\n', 1)[1])
        self.assertEqual(template['base_snapshot'], assignment['base_snapshot'])
        self.assertEqual(template['request_id'], 'replace-with-a-new-unique-id')
        self.assertEqual(sum(1 for item in template['evidence'] if item['role'] == 'result'), 1)
        self.assertNotIn('sha256', template['evidence'][0])


if __name__ == '__main__':
    unittest.main()
