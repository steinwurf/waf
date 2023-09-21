import os
import mock

from wurf.git_checkout_resolver import GitCheckoutResolver


def test_git_checkout_resolver(testdirectory):
    ctx = mock.Mock()
    git = mock.Mock()
    dependency = mock.Mock()
    cwd = testdirectory.path()

    # Create a parent folder for the dependency and the corresponding
    # subfolder for the 'master' checkout
    repo_folder = testdirectory.mkdir("links-01234")
    master_folder = repo_folder.mkdir("master")

    git_resolver = mock.Mock()
    git_resolver.resolve.return_value = master_folder.path()

    dependency.name = "links"
    checkout = "my-branch"

    git.branches = mock.Mock(return_value=["master", checkout])

    resolver = GitCheckoutResolver(
        git=git,
        resolver=git_resolver,
        ctx=ctx,
        dependency=dependency,
        cwd=cwd,
        checkout=checkout,
    )

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

    assert git.checkout.called is False
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

    assert git.checkout.called is False
    assert git.pull.called is False
    git.pull_submodules.assert_called_once_with(cwd=path)
