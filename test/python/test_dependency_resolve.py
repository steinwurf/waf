
# Make sure we can load the bundle_dependency.py
import sys
sys.path.append('../../tools')
sys.path.append('../../python-semver')

import unittest
import dependency_resolve as dr
import mock
import os


class TestResolveGitMajorVersion(unittest.TestCase):

    def test_select_tag(self):
        tags = ['2.3.4', '1.0.0', '1.3.5', '1.0.1', '2.0.0', '1.1.2']

        # Major version 1
        resolver = dr.ResolveGitMajorVersion(name="test",
                                             git_repository="git://dummy.git",
                                             major_version=1)

        tag = resolver.select_tag(tags)
        self.assertEqual(tag, '1.3.5')

        # Major version 2
        resolver = dr.ResolveGitMajorVersion(name="test",
                                             git_repository="git://dummy.git",
                                             major_version=2)

        tag = resolver.select_tag(tags)
        self.assertEqual(tag, '2.3.4')

    def test_resolve(self):
        resolver = dr.ResolveGitMajorVersion(name="test",
                                             git_repository="git://dummy.git",
                                             major_version=1)

        m = mock.Mock()
        m.git_tags = mock.Mock(return_value=['1.0.0', '1.2.3', '1.2.0'])

        repo_dir = os.path.abspath(os.path.expanduser('~/here'))

        resolver.resolve(m, repo_dir)

        # Check function calls
        self.assertEqual(m.method_calls[0], (
            'git_clone', ('git://dummy.git', repo_dir + '/test-master'),
            {'cwd': repo_dir}))

        self.assertEqual(m.method_calls[1], (
            'git_pull', (),
            {'cwd': repo_dir + '/test-master'}))

        # We don't see the call to git_tags() here since we mocked it
        # out above

        self.assertEqual(m.method_calls[2], (
            'git_local_clone', (repo_dir + '/test-master',
                                repo_dir + '/test-1.2.3'),
            {'cwd': repo_dir}))

        self.assertEqual(m.method_calls[3], (
            'git_checkout', ('1.2.3',),
            {'cwd': repo_dir + '/test-1.2.3'}))

        # print m.method_calls

if __name__ == '__main__':
    unittest.main()
