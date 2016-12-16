import pytest
import mock

from wurf.wurf_hash_manager import WurfHashManager

def test_wurf_hash_manager():

    m = WurfHashManager()

    kwargs1 = {'foo': 'b', 'bar': 'a'}
    kwargs2 = {'bar': 'a', 'foo': 'b'}

    class FakeManager(object):

        def __init__(self, args):
            self.args = args

        def add_dependency(self, sha1, **kwargs):

            assert(kwargs == self.args)
            self.sha1 = sha1

    f1 = FakeManager(kwargs1)
    m.next_resolver = f1

    m.add_dependency(**kwargs1)

    f2 = FakeManager(kwargs2)
    m.next_resolver = f2

    m.add_dependency(**kwargs2)

    assert(f1.sha1 == f2.sha1)
