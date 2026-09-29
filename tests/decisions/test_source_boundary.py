"""Synthetic body-read counterexamples through the actual loading facade."""
from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from engine.decisions.load import load_projection
from engine.decisions.model import Refusal, byte_digest, canonical, digest, validate
from engine.decisions.shadow import public_receipt, run_private_shadow, run_public_shadow
from test_decisions import fixture, reseal


class SourceBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.public, self.private = self.root/'public', self.root/'private'
        (self.public/'canon').mkdir(parents=True)
        (self.private/'overlays').mkdir(parents=True)
        self.policies, self.snapshot, self.sources = fixture()
        self.args = dict(public_repository=self.public, private_repository=self.private,
                         actor='synthetic-actor-secret', tenant='synthetic-tenant-secret',
                         trusted_authorities={'fixture-authority'}, now=150)
        self.bundle = {'schema':'DecisionSourceBundle/v1', 'purpose':'offline_fixture_not_admission',
                       'valid_from':100,'expires_at':200,'snapshot':self.snapshot,
                       'snapshot_digest':digest(self.snapshot),'required_sources':[],
                       'revoked_digests':[],'entries':[]}
        for i, pin in enumerate(self.snapshot['policies']):
            self.add_entry('policy', f'policy-{i}', canonical(self.policies[pin['id']]),
                           private=i>0, scope=pin['scope'], parent=self.policies[pin['id']]['parent'],
                           policy_pin=pin)
        for i, source in enumerate(self.snapshot['sources']):
            self.add_entry('source', f'source-{i}', self.sources[source['digest']],
                           private=i==0, scope=self.snapshot['policies'][0]['scope'], parent=None,
                           source_ref=source)
        self.seal()
        self.prepare_request()

    def add_entry(self, kind, name, data, *, private, scope, parent, **binding):
        relative = ('overlays/' if private else 'canon/') + name + '.json'
        entry = dict(id=name, revision='test-r1', digest=byte_digest(data), authority='fixture-authority',
                     scope=scope, parent=parent, classification='private_overlay' if private else 'public_base',
                     path=relative, required=True, valid_from=100, expires_at=200,
                     access=dict(actor=self.args['actor'] if private else '*',
                                 tenant=self.args['tenant'] if private else '*',
                                 decision='allow',purpose='offline_fixture_not_grant'),kind=kind,**binding)
        self.bundle['entries'].append(entry)
        self.bundle['required_sources'].append(name)
        ((self.private if private else self.public)/relative).write_bytes(data)

    def seal(self):
        self.bundle['snapshot_digest'] = digest(self.snapshot)
        self.args['expected_bundle_digest'] = digest(self.bundle)

    def load(self):
        return load_projection(self.bundle, **self.args)

    def private_run(self, verdict='allow'):
        return run_private_shadow(self.bundle, self.request, self.evidence,
                                  deterministic_verdict=verdict, **self.args)

    def public_run(self):
        return run_public_shadow(self.bundle, self.request, self.evidence,
                                 deterministic_verdict='allow', **self.args)

    def prepare_request(self):
        projection = self.load()
        state = {'task_goal':'synthetic-private-body', 'remaining_work':'synthetic-private-work',
                 'risk_class':'low'}
        self.request = dict(schema='DecisionRequest/v1',id='synthetic-private-request',
                            decision_type='model.tier',projection_digest=projection['digest'],
                            scope=projection['projection']['scope'],state=state,state_digest=digest(state),
                            candidates=['economy','balanced','high_assurance'],baseline='balanced')
        self.evidence = dict(schema='DecisionEvidence/v1',request_digest=digest(self.request),
                             provider='synthetic-private-provider',model='synthetic-private-model',
                             model_version='test-r1',primitive='choice',score_semantics='normalized_option_mass',
                             values_ppm=dict(economy=1000000,balanced=0,high_assurance=0),
                             calibration='not_measured',abstain=False)

    def refresh_policy_files(self):
        # Change the independently pinned test inputs, never silently repin production.
        reseal(self.policies, self.snapshot)
        for entry in self.bundle['entries']:
            if entry['kind'] == 'policy':
                p = self.policies[entry['policy_pin']['id']]
                entry['parent'] = p['parent']
                data = canonical(p)
                entry['digest'] = byte_digest(data)
                root = self.public if entry['classification']=='public_base' else self.private
                (root/entry['path']).write_bytes(data)
        self.seal()

    def test_actual_loader_combines_required_public_and_private_closure(self):
        result = self.private_run()
        validate('trace',result)
        self.assertEqual(result['recommended'],['economy'])
        self.assertFalse(result['authorization_granted'])
        self.assertFalse(result['applied'])
        self.assertEqual(result['mode'],'offline_shadow')
        self.assertIn('extra-obligation-1',result['mandatory'])
        self.assertIn('extra-obligation-2',result['mandatory'])

    def test_actor_and_tenant_denied_before_any_body_read(self):
        for field in ['actor','tenant']:
            with self.subTest(field=field), patch('engine.decisions.load._read', side_effect=AssertionError('unexpected body read')) as read:
                args = dict(self.args, **{field:'foreign'})
                with self.assertRaisesRegex(Refusal,'BODY_READ_DENIED'):
                    load_projection(self.bundle,**args)
                read.assert_not_called()

    def test_denied_or_unknown_required_overlay_never_falls_back(self):
        for decision in ['deny','unknown']:
            with self.subTest(decision=decision), patch('engine.decisions.load._read', side_effect=AssertionError('unexpected body read')) as read:
                self.bundle['entries'][1]['access']['decision'] = decision
                self.seal()
                with self.assertRaisesRegex(Refusal,'BODY_READ_DENIED'):
                    self.load()
                read.assert_not_called()

    def test_missing_required_overlay_refuses(self):
        (self.private/self.bundle['entries'][1]['path']).unlink()
        with self.assertRaisesRegex(Refusal,'SOURCE_UNAVAILABLE'):
            self.load()

    def test_missing_descriptor_refuses_even_if_resealed(self):
        self.bundle['entries'].pop(1)
        self.seal()
        with self.assertRaisesRegex(Refusal,'REQUIRED_CLOSURE_MISMATCH'):
            self.load()

    def test_missing_closure_member_cannot_be_hidden_by_manifest_reseal(self):
        removed = self.bundle['entries'].pop(1)
        self.bundle['required_sources'].remove(removed['id'])
        self.seal()
        with self.assertRaisesRegex(Refusal,'POLICY_CLOSURE_MISMATCH'):
            self.load()

    def test_unknown_classification_refuses(self):
        self.bundle['entries'][1]['classification'] = 'confidential'
        self.seal()
        with self.assertRaisesRegex(Refusal,'INVALID_SOURCE_BUNDLE'):
            self.load()

    def test_mixed_roots_refuse(self):
        for root in [self.public, self.public/'canon', self.public.parent]:
            with self.subTest(root=root), self.assertRaisesRegex(Refusal,'MIXED_SOURCE_ROOTS'):
                load_projection(self.bundle,**dict(self.args, private_repository=root))

    def test_wrong_class_path_is_not_hydrated(self):
        for index,path in [(0,'overlays/private.json'),(1,'canon/base.json')]:
            old=self.bundle['entries'][index]['path']
            self.bundle['entries'][index]['path']=path
            self.seal()
            with self.subTest(index=index), patch('engine.decisions.load._read', side_effect=AssertionError('unexpected body read')) as read:
                with self.assertRaisesRegex(Refusal,'SOURCE_ROOT_EXCLUDED'):
                    self.load()
                read.assert_not_called()
            self.bundle['entries'][index]['path']=old

    def test_candidate_traversal_and_absolute_paths_at_loader(self):
        paths=['proposals/x.json','generated/x.json','tests/x.json','compiler/x.json',
               'canon/../proposals/x.json','canon//x.json','canon/./x.json',
               '/canon/x.json','canon\\x.json','canon/x\x00.json']
        for path in paths:
            self.bundle['entries'][0]['path']=path
            self.seal()
            with self.subTest(path=path), self.assertRaises(Refusal):
                self.load()

    def test_symlink_file_and_directory_at_loader(self):
        entry=self.bundle['entries'][0]
        source=self.public/entry['path']
        outside=self.root/'candidate.json'; outside.write_bytes(source.read_bytes())
        source.unlink(); source.symlink_to(outside)
        with self.assertRaisesRegex(Refusal,'SOURCE_UNAVAILABLE'):
            self.load()
        source.unlink()
        folder=self.public/'canon/link'; folder.symlink_to(self.root,target_is_directory=True)
        entry['path']='canon/link/candidate.json'; self.seal()
        with self.assertRaisesRegex(Refusal,'SOURCE_UNAVAILABLE'):
            self.load()

    def test_symlink_repository_root_refuses(self):
        link=self.root/'root-link'; link.symlink_to(self.public,target_is_directory=True)
        with self.assertRaisesRegex(Refusal,'SOURCE_UNAVAILABLE'):
            load_projection(self.bundle,**dict(self.args,public_repository=link))

    def test_hardlink_and_fifo_do_not_escape_regular_file_gate(self):
        entry=self.bundle['entries'][0]; source=self.public/entry['path']
        os.link(source,self.root/'aliased-policy')
        with self.assertRaisesRegex(Refusal,'SOURCE_FILE_EXCLUDED'):
            self.load()
        source.unlink(); os.mkfifo(source)
        with self.assertRaisesRegex(Refusal,'SOURCE_FILE_EXCLUDED'):
            self.load()

    def test_stale_and_revoked_base_or_overlay(self):
        for index in [0,1]:
            entry=self.bundle['entries'][index]
            entry['expires_at']=150; self.seal()
            with self.subTest(index=index), self.assertRaisesRegex(Refusal,'STALE_SOURCE'):
                self.load()
            entry['expires_at']=200
            self.bundle['revoked_digests']=[entry['digest']]; self.seal()
            with self.subTest(index=index), self.assertRaisesRegex(Refusal,'REVOKED_SOURCE'):
                self.load()
            self.bundle['revoked_digests']=[]

    def test_revoked_snapshot_base_or_overlay_through_loader(self):
        for index in [0,1]:
            self.snapshot['revoked_digests']=[self.snapshot['policies'][index]['digest']]
            self.seal()
            with self.assertRaisesRegex(Refusal,'REVOKED_PIN'):
                self.load()

    def test_stale_bundle_and_snapshot_through_loader(self):
        self.bundle['expires_at']=150; self.seal()
        with self.assertRaisesRegex(Refusal,'STALE_BUNDLE'):
            self.load()
        self.bundle['expires_at']=200; self.snapshot['expires_at']=150; self.seal()
        with self.assertRaisesRegex(Refusal,'STALE_SNAPSHOT'):
            self.load()

    def test_changed_parent_refuses_through_loader(self):
        self.bundle['entries'][1]['parent']={'id':'forged','digest':'sha256:'+'0'*64}
        self.seal()
        with self.assertRaisesRegex(Refusal,'SOURCE_PARENT_MISMATCH'):
            self.load()

    def test_wrong_source_revision_scope_authority_and_external_pin(self):
        for field,value,code in [('revision','other','SOURCE_IDENTITY_MISMATCH'),
                                  ('scope',{'level':'project','id':'foreign'},'SOURCE_SCOPE_MISMATCH'),
                                  ('authority','self-admitted','UNKNOWN_AUTHORITY')]:
            entry=self.bundle['entries'][-1]; old=entry[field]; entry[field]=value; self.seal()
            with self.subTest(field=field), self.assertRaisesRegex(Refusal,code):
                self.load()
            entry[field]=old
        self.seal(); self.bundle['expires_at']=201
        with self.assertRaisesRegex(Refusal,'BUNDLE_PIN_MISMATCH'):
            self.load()

    def test_changed_file_bytes_do_not_pass_loader(self):
        (self.public/self.bundle['entries'][0]['path']).write_bytes(b'{}')
        with self.assertRaisesRegex(Refusal,'SOURCE_BYTES_MISMATCH'):
            self.load()

    def test_semantically_equal_file_still_needs_exact_byte_pin(self):
        path = self.public/self.bundle['entries'][0]['path']
        path.write_bytes(path.read_bytes()+b'\n')
        with self.assertRaisesRegex(Refusal,'SOURCE_BYTES_MISMATCH'):
            self.load()

    def test_lower_scope_weakening_refuses_through_loader(self):
        root,child=list(self.policies.values())[:2]
        child['decisions']=deepcopy(root['decisions'])
        child['decisions'][0]['threshold_ppm']=1
        self.refresh_policy_files()
        with self.assertRaisesRegex(Refusal,'INHERITED_DECISION_CONFLICT'):
            self.load()

    def test_model_confidence_cannot_override_deterministic_denial(self):
        for verdict in ['deny','unknown']:
            result=self.private_run(verdict)
            self.assertEqual(result['policy_action'],'deny')
            self.assertEqual(result['recommended'],[])
            self.assertFalse(result['authorization_granted'])

    def test_public_output_excludes_all_private_trace_fields_and_digests(self):
        internal=self.private_run()
        self.assertIn('synthetic-private-provider',json.dumps(internal))
        expected={'schema':'PublicDecisionBoundary/v1','mode':'offline_shadow',
                  'applied':False,'authorization_granted':False,
                  'publication_enabled':False,'result':'withheld'}
        self.assertEqual(self.public_run(),expected)
        self.assertEqual(public_receipt(),expected)
        self.bundle['entries'][1]['access']['decision']='deny'; self.seal()
        self.assertEqual(self.public_run(),expected)
        # Different low-entropy private body, same public serialization.
        self.bundle['entries'][1]['access']['decision']='allow'; self.seal()
        (self.private/self.bundle['entries'][1]['path']).write_bytes(b'yes')
        self.assertEqual(self.public_run(),expected)

    def test_public_constant_does_not_alias_internal_state(self):
        result=self.public_run(); result['mode']='changed'
        self.assertEqual(self.public_run()['mode'],'offline_shadow')


if __name__=='__main__':
    unittest.main()
