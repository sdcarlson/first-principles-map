import copy
import json
import unittest
from pathlib import Path
from check import check, Fail

class GraphValidationTests(unittest.TestCase):
    def setUp(self):
        self.graph = json.loads(Path(__file__).with_name('graph.json').read_text(encoding='utf-8'))

    def rejected(self, change, message):
        change(self.graph)
        with self.assertRaisesRegex(Fail, message):
            check(self.graph)

    def test_current_map(self):
        check(self.graph)

    def test_duplicate_node(self):
        self.rejected(lambda g: g['nodes'].append(copy.deepcopy(g['nodes'][0])), 'duplicate id')

    def test_missing_source(self):
        self.rejected(lambda g: g['nodes'][0]['sources'][0].update(id='missing'), 'unknown source')

    def test_unsafe_source(self):
        self.rejected(lambda g: g['sources'][0].update(url='javascript:alert(1)'), 'unsafe URL')

    def test_missing_limits(self):
        self.rejected(lambda g: g['nodes'][0].update(limits=''), 'nonempty text')

    def test_model_assumptions(self):
        self.rejected(lambda g: next(n for n in g['nodes'] if n['kind']=='model').update(assumptions=[]), 'needs assumptions')

    def test_unsupported_edge(self):
        self.rejected(lambda g: g['edges'][0].update(sources=[]), 'needs sources')

    def test_dangling_edge(self):
        self.rejected(lambda g: g['edges'][0].update(dst='missing'), 'dangling edge')

    def test_duplicate_edge(self):
        self.rejected(lambda g: g['edges'].append(copy.deepcopy(g['edges'][0])), 'duplicate edge')

    def test_false_deduction(self):
        self.rejected(lambda g: g['edges'][0].update(type='derives'), 'unknown edge relation')

    def test_gap_is_not_evidence(self):
        self.rejected(lambda g: g['edges'][0].update(src='measurement'), 'evidence relation')

    def test_bad_path_reference(self):
        self.rejected(lambda g: g['paths'][0]['nodes'].append('missing'), 'unknown node')

    def test_disconnected_path(self):
        self.rejected(lambda g: g['paths'][0]['nodes'].append('citrate'), 'disconnected reading path')

    def test_missing_citation_scope(self):
        self.rejected(lambda g: g['nodes'][0]['sources'][0].update(supports=''), 'citation scope')

if __name__ == '__main__':
    unittest.main()
