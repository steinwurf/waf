# Make sure we can load the bundle_dependency.py
import sys
import unittest
import wurf_dependency_resolve as dr
import mock
import os


class TestResolveGitMajorVersion(unittest.TestCase):

    def test_select_tag(self):
        tags = ['2.3.4', '1.0.0', '1.3.5', '1.0.1', '2.0.0', '1.1.2', '1.1.1',
                '3.0.0', '3.0.0-lts.0', '3.0.0-lts.1']

        # Major version 1
        resolver = dr.ResolveVersion(name="test",
                                     git_repository="dummy.git",
                                     major=1)

        tag = resolver.select_tag(tags)
        self.assertEqual(tag, '1.3.5')

        # Major version 2
        resolver = dr.ResolveVersion(name="test",
                                     git_repository="dummy.git",
                                     major=2)

        tag = resolver.select_tag(tags)
        self.assertEqual(tag, '2.3.4')

        # Major minor version 1
        resolver = dr.ResolveVersion(name="test",
                                     git_repository="dummy.git",
                                     major=1,
                                     minor=1)

        tag = resolver.select_tag(tags)
        self.assertEqual(tag, '1.1.2')

        # Major minor patch version 1
        resolver = dr.ResolveVersion(name="test",
                                     git_repository="dummy.git",
                                     major=1,
                                     minor=1,
                                     patch=1)

        tag = resolver.select_tag(tags)
        self.assertEqual(tag, '1.1.1')

        # Major version 2
        resolver = dr.ResolveVersion(name="test",
                                     git_repository="dummy.git",
                                     major=2)

        tag = resolver.select_tag(tags)
        self.assertEqual(tag, '2.3.4')

        # Major version 3 (ignoring LTS tags)
        resolver = dr.ResolveVersion(name="test",
                                     git_repository="dummy.git",
                                     major=3)

        tag = resolver.select_tag(tags)
        self.assertEqual(tag, '3.0.0')

    def test_resolve(self):
        resolver = dr.ResolveVersion(name="test",
                                     git_repository="dummy.git",
                                     major=1)

        m = mock.Mock()
        m.git_tags = mock.Mock(return_value=['1.0.0', '1.2.3', '1.2.0'])
        dr.git_protocol_handler = 'git://'
        repo_dir = os.path.abspath(os.path.expanduser('~/here'))

        #resolver.resolve(
        #    ctx=m,
        #    path=repo_dir,
        #    use_checkout=None)

        # Check function calls
        #self.assertEqual(m.method_calls[1], (
        #    'git_clone', ('git://dummy.git', repo_dir + '/test-9199d9/master'),
        #    {'cwd': repo_dir + '/test-9199d9'}))

        #self.assertEqual(m.method_calls[1],
        #    ('git_pull', (), {'cwd': repo_dir + '/test-9199d9/master'}))

if __name__ == '__main__':
    unittest.main()
