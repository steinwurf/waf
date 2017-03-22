import os
import pytest
import mock

from wurf.git_checkout_resolver import GitCheckoutResolver


def test_git_checkout_resolver(test_directory):

    ctx = mock.Mock()
    git = mock.Mock()
    dependency = mock.Mock()
    cwd = test_directory.path()

    # Create a parent folder for the dependency and the corresponding
    # subfolder for the 'master' checkout
    repo_folder = test_directory.mkdir('links-01234')
    master_folder = repo_folder.mkdir('master')

    git_resolver = mock.Mock()
    git_resolver.resolve.return_value = master_folder.path()

    dependency.name = 'links'
    checkout = 'my-branch'
    repo_url = 'https://gitlab.com/steinwurf/links.git'

    resolver = GitCheckoutResolver(git=git, git_resolver=git_resolver,
        ctx=ctx, dependency=dependency, checkout=checkout)

    path = resolver.resolve()

    # The checkout path should now exist
    assert os.path.isdir(path)

    git.checkout.assert_called_once_with(branch=checkout, cwd=path)
    git.pull_submodules.assert_called_once_with(cwd=path)

    # Reset the git mock
    git.reset_mock()
    # Simulate a normal branch (non-detached head)
    git.is_detached_head.return_value = False

    # The destination folder is already created, so the next resolve
    # should just run git pull
    path2 = resolver.resolve()

    assert path2 == path

    assert git.checkout.called == False
    git.pull.assert_called_once_with(cwd=path)
    git.pull_submodules.assert_called_once_with(cwd=path)

    # Reset the git mock
    git.reset_mock()
    # Simulate a tag or a commit (detached head)
    git.is_detached_head.return_value = True

    # The destination folder is already created, so the next resolve
    # should just run git pull
    path3 = resolver.resolve()

    assert path3 == path

    assert git.checkout.called == False
    assert git.pull.called == False
    git.pull_submodules.assert_called_once_with(cwd=path)
