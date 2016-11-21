import pytest
import mock
import os

from wurf.wurf_git_checkout_resolver import WurfGitCheckoutResolver

def test_wurf_git_checkout_resolver(test_directory):

    return

    # Lets create a dir for the git resolver
    master_director = test_directory.mkdir('bla-master-01234')

    git_resolver = mock.Mock()
    git_resolver.resolve.return_value = master_director.path()

    resolver = WurfGitCheckoutResolver(
        name='links',
        checkout='my-branch',
        git_resolver=git_resolver,
        log=mock.Mock())

    ctx = mock.Mock()
    cwd = test_directory.path()

    path = resolver.resolve(ctx, cwd)

    # Given  /tmp/test_wurf_git_resolver0/links-bla-04aeea yields:
    #
    #    links-bla-04aeea
    #
    # The destination is computed in the resolve function we just get it here
    # manually.
    destination = os.path.basename(os.path.normpath(path))

    # The path should now exist
    assert(os.path.isdir(path))

    ctx.git_checkout.assert_called_once_with(branch='my-branch', cwd=path)
    ctx.git_get_submodules.assert_called_once_with(repository_dir=path)

    # Lets try to create the destination folder and check if we just pull:
    # Reset our context
    ctx = mock.Mock()
    ctx.git_default_scheme.return_value=None

    path = resolver.resolve(ctx, cwd)

    ctx.git_pull.assert_called_once_with(cwd=path)
    ctx.git_get_submodules.assert_called_once_with(repository_dir=path)
