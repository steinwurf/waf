import os
import pytest
import mock

from wurf.git_semver_resolver import GitSemverResolver


def test_git_semver_resolver(test_directory):

    ctx = mock.Mock()
    git = mock.Mock()
    cwd = test_directory.path()

    # Create a parent folder for the dependency and the corresponding
    # subfolder for the 'master' checkout
    repo_folder = test_directory.mkdir('links')
    master_folder = repo_folder.mkdir('master-01234')

    dependency = mock.Mock()
    dependency.name = 'links'
    dependency.major = 5
    selected_tag = '5.1.0'
    repo_url = 'https://gitlab.com/steinwurf/links.git'

    git_resolver = mock.Mock()
    git_resolver.resolve.return_value = master_folder.path()

    semver_selector = mock.Mock()
    semver_selector.select_tag.return_value = selected_tag

    resolver = GitSemverResolver(git=git, git_resolver=git_resolver,
        ctx=ctx, semver_selector=semver_selector,working_path=repo_folder.path(),
        dependency=dependency)

    path = resolver.resolve()

    # The checkout path should now exist
    assert os.path.isdir(path)

    git.tags.assert_called_once_with(cwd=master_folder.path())
    git.checkout.assert_called_once_with(branch=selected_tag, cwd=path)
    git.pull_submodules.assert_called_once_with(cwd=path)
