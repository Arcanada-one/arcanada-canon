"""Scope ownership counterexamples using fully pinned synthetic registries."""
from copy import deepcopy
import unittest
from unittest.mock import patch

from engine.decisions import Refusal, digest, resolve
from engine.decisions.model import byte_digest, canonical, load_json
from engine.decisions.shadow import public_receipt
from test_decisions import fixture
import test_source_boundary as source_boundary


def replace_registry(snapshot, sources, chains):
    """Repin deliberately changed fixture inputs, never production data."""
    old = snapshot['registry_pin']['digest']
    registry = load_json(sources[old])
    registry['scope_chains'] = deepcopy(chains)
    data = canonical(registry)
    pin = dict(snapshot['registry_pin'], digest=byte_digest(data))
    snapshot['registry_pin'] = pin
    snapshot['sources'] = [pin if s['digest'] == old else s for s in snapshot['sources']]
    snapshot['source_digests'] = [pin['digest'] if p == old else p for p in snapshot['source_digests']]
    sources.pop(old)
    sources[pin['digest']] = data
    return old, pin, data


class HierarchyTests(unittest.TestCase):
    def setUp(self):
        self.policies, self.snapshot, self.sources = fixture(5)
        self.chain = [deepcopy(p['scope']) for p in self.snapshot['policies']]

    def resolve(self, chains):
        replace_registry(self.snapshot, self.sources, chains)
        return resolve(self.policies, self.snapshot,
                       expected_snapshot_digest=digest(self.snapshot),
                       target_scope=self.chain[-1], sources=self.sources, now=150)

    def test_project_cannot_have_two_spaces_even_when_both_chains_are_pinned(self):
        other = deepcopy(self.chain)
        other[1]['id'] = 'other-space'
        with self.assertRaisesRegex(Refusal, 'AMBIGUOUS_SCOPE_PARENT'):
            self.resolve([self.chain, other])

    def test_conflict_is_order_independent(self):
        other = deepcopy(self.chain)
        other[1]['id'] = 'other-space'
        with self.assertRaisesRegex(Refusal, 'AMBIGUOUS_SCOPE_PARENT'):
            self.resolve([other, self.chain])

    def test_unrelated_conflicting_projects_also_refuse(self):
        one = deepcopy(self.chain[:3]); one[-1]['id'] = 'unrelated-project'
        two = deepcopy(one); two[1]['id'] = 'another-space'
        with self.assertRaisesRegex(Refusal, 'AMBIGUOUS_SCOPE_PARENT'):
            self.resolve([self.chain, one, two])

    def test_one_registry_cannot_mix_universes(self):
        other = deepcopy(self.chain)
        for scope in other:
            scope['id'] = 'another-' + scope['id']
        with self.assertRaisesRegex(Refusal, 'MULTIPLE_SCOPE_UNIVERSES'):
            self.resolve([self.chain, other])

    def test_unselected_skipped_rung_refuses(self):
        with self.assertRaisesRegex(Refusal, 'INVALID_REGISTERED_SCOPE_CHAIN'):
            self.resolve([self.chain, [self.chain[0], self.chain[2]]])

    def test_unselected_wrong_order_refuses(self):
        with self.assertRaisesRegex(Refusal, 'INVALID_REGISTERED_SCOPE_CHAIN'):
            self.resolve([self.chain, [self.chain[1], self.chain[0]]])

    def test_unselected_repeated_level_refuses(self):
        wrong = deepcopy(self.chain[:2]); wrong[1]['level'] = 'universe'
        with self.assertRaisesRegex(Refusal, 'INVALID_REGISTERED_SCOPE_CHAIN'):
            self.resolve([self.chain, wrong])

    def test_shared_prefixes_and_contextual_role_names_are_valid(self):
        other = deepcopy(self.chain)
        other[2]['id'] = 'second-project'
        result = self.resolve([self.chain[:1], self.chain[:2], self.chain, other])
        self.assertEqual(result['projection']['scope'], self.chain[-1])
        self.assertFalse(result['projection']['publication_enabled'])
        self.assertIn('extra-obligation-2', result['projection']['mandatory'])

    def test_same_text_at_different_levels_is_not_identity_collision(self):
        other = deepcopy(self.chain[:3])
        other[2]['id'] = other[1]['id']
        self.assertEqual(self.resolve([self.chain, other])['projection']['mode'], 'offline_shadow')

    def test_distinct_projects_in_distinct_spaces_are_valid(self):
        other = deepcopy(self.chain[:3]); other[1]['id'] = 'other-space'; other[2]['id'] = 'other-project'
        self.assertEqual(self.resolve([other, self.chain])['projection']['scope'], self.chain[-1])

    def test_same_project_prefix_and_full_chain_are_valid(self):
        self.assertEqual(len(self.resolve([self.chain[:3], self.chain])['projection']['lineage']), 5)

    def test_registry_size_is_bounded(self):
        chains = [self.chain]
        for i in range(1024):
            other = deepcopy(self.chain[:3]); other[2]['id'] = f'project-{i}'
            chains.append(other)
        with self.assertRaisesRegex(Refusal, 'INVALID_BINDINGS'):
            self.resolve(chains)

    def test_parent_conflict_is_a_constant_code_without_identity(self):
        other = deepcopy(self.chain); other[1]['id'] = 'private-space-name'
        with self.assertRaises(Refusal) as caught:
            self.resolve([self.chain, other])
        self.assertEqual(str(caught.exception), 'AMBIGUOUS_SCOPE_PARENT')


class LoaderHierarchyTests(unittest.TestCase):
    def setUp(self):
        # Reuse fixture construction, not its test methods or result counts.
        self.context = source_boundary.SourceBoundaryTests()
        self.context.setUp()
        self.addCleanup(self.context.doCleanups)

    def conflict(self):
        c = self.context
        chain = [deepcopy(p['scope']) for p in c.snapshot['policies']]
        other = deepcopy(chain); other[1]['id'] = 'other-private-space'
        old, pin, data = replace_registry(c.snapshot, c.sources, [chain, other])
        entry = next(e for e in c.bundle['entries'] if e['kind'] == 'source' and e['digest'] == old)
        entry['source_ref'] = pin
        entry['digest'] = pin['digest']
        (c.public / entry['path']).write_bytes(data)
        c.seal()

    def test_native_loader_refuses_fully_resealed_matrix_membership(self):
        self.conflict()
        with self.assertRaisesRegex(Refusal, 'AMBIGUOUS_SCOPE_PARENT'):
            self.context.load()

    def test_private_shadow_refuses_before_probability_evaluation(self):
        self.conflict()
        with patch('engine.decisions.shadow.evaluate', side_effect=AssertionError('evaluation reached')) as model:
            with self.assertRaisesRegex(Refusal, 'AMBIGUOUS_SCOPE_PARENT'):
                self.context.private_run()
            model.assert_not_called()

    def test_public_result_is_identical_on_valid_and_conflicting_registry(self):
        valid = self.context.public_run()
        self.conflict()
        self.assertEqual(valid, public_receipt())
        self.assertEqual(self.context.public_run(), valid)


if __name__ == '__main__':
    unittest.main()
