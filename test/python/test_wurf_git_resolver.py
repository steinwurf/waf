import pytest
import mock

from wurf_git_resolver import WurfGitSResolver

def test_wurf_git_resolver(test_directory):

    resolver = WurfGitSResolver(name='test',
                                url='gitlab.com/steinwurf/links.git',
                                log=mock.Mock())

    ctx = mock.Mock()
    cwd = test_directory.path()

    path = resolver.resolve(ctx, cwd)
