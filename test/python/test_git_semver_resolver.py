import os
import mock

from wurf.git_semver_resolver import GitSemverResolver


def test_git_semver_resolver(testdirectory):

    ctx = mock.Mock()
    git = mock.Mock()
    cwd = testdirectory.path()

    # Create a parent folder for the dependency and the corresponding
    # subfolder for the 'master' checkout
    repo_folder = testdirectory.mkdir("links-01234")
    master_folder = repo_folder.mkdir("master")

    dependency = mock.Mock()
    dependency.name = "links"
    dependency.major = 5
    selected_tag = "5.1.0"

    git_resolver = mock.Mock()
    git_resolver.resolve.return_value = master_folder.path()

    semver_selector = mock.Mock()
    semver_selector.select_tag.return_value = selected_tag

    resolver = GitSemverResolver(
        git=git,
        resolver=git_resolver,
        ctx=ctx,
        semver_selector=semver_selector,
        dependency=dependency,
        cwd=cwd,
    )

    path = resolver.resolve()

    # The checkout path should now exist
    assert os.path.isdir(path)

    git.tags.assert_called_once_with(cwd=master_folder.path())
    git.checkout.assert_called_once_with(branch=selected_tag, cwd=path)
    git.pull_submodules.assert_called_once_with(cwd=path)
