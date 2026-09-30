"""Native offline loader/shadow process canary; synthetic pinned source bodies."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.decisions.model import Refusal
from engine.decisions.shadow import public_receipt
from test_hierarchy import LoaderHierarchyTests


def main():
    probe = LoaderHierarchyTests()
    probe.setUp()
    try:
        valid = probe.context.private_run()
        assert valid['mode'] == 'offline_shadow'
        assert valid['applied'] is False and valid['authorization_granted'] is False
        assert 'extra-obligation-2' in valid['mandatory']
        public_before = probe.context.public_run()
        probe.conflict()
        try:
            probe.context.load()
        except Refusal as failure:
            assert str(failure) == 'AMBIGUOUS_SCOPE_PARENT'
        else:
            raise AssertionError('matrix project membership reached the consumer')
        assert probe.context.public_run() == public_before == public_receipt()
        print(json.dumps({'schema': 'HierarchyConsumerCanary/v1', 'verdict': 'verified',
                          'positive': 'required obligations retained',
                          'negative': 'matrix project refused',
                          'public_boundary': 'constant', 'model_calls': 0,
                          'source': 'synthetic pinned files', 'mode': 'offline_shadow'}))
    finally:
        probe.doCleanups()


if __name__ == '__main__':
    main()
