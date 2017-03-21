import os
import pytest
import mock
import shutil

from wurf.existing_tag_resolver import ExistingTagResolver
from wurf.git_semver_resolver import GitSemverResolver


def test_existing_tag_resolver(test_directory):

    ctx = mock.Mock()

    dependency = mock.Mock()
    dependency.name = 'foo'
    dependency.major = 5
    latest_tag = '5.1.0'
    # The sources should contain the 'steinwurf' string, otherwise the
    # ExistingTagResolver will ignore them
    sources = ['steinwurf-url1', 'steinwurf-url2']

    # ExistingTagResolver will enumerate the parent folder for each source,
    # so we create these parent folders
    repo_folder1 = test_directory.mkdir('foo-steinwurf-url1')
    repo_folder2 = test_directory.mkdir('foo-steinwurf-url2')

    semver_selector = mock.Mock()
    semver_selector.select_tag.return_value = latest_tag

    tag_database = mock.Mock()
    tag_database.project_tags.return_value = ['5.1.0', '5.0.0']

    def repo_folder(name, source):
        folder_name = '{}-{}'.format(name, source)
        return os.path.join(test_directory.path(), folder_name)

    parent_folder = mock.Mock()
    parent_folder.parent_folder.side_effect = repo_folder

    resolver = ExistingTagResolver(ctx=ctx, dependency=dependency,
        semver_selector=semver_selector, tag_database=tag_database,
        parent_folder=parent_folder, sources=sources)

    # The parent folders are empty, so the resolver should return None
    path = resolver.resolve()
    assert path == None

    older_tag_folder = repo_folder1.mkdir('5.0.0')
    # The latest tag is still not present, the resolver should return None
    path = resolver.resolve()
    assert path == None

    latest_tag_folder = repo_folder1.mkdir('5.1.0')
    # Now the latest tag is present in repo_folder1
    path = resolver.resolve()
    assert path == latest_tag_folder.path()

    # Remove the latest tag from repo_folder1, and create it in repo_folder2
    shutil.rmtree(latest_tag_folder.path())
    latest_tag_folder2 = repo_folder2.mkdir('5.1.0')

    # Now the latest tag is only present in repo_folder2
    path = resolver.resolve()
    assert path == latest_tag_folder2.path()

def test_existing_tag_resolver_with_semver(test_directory):

    ctx = mock.Mock()
    git = mock.Mock()
    cwd = test_directory.path()

    # Create a parent folder for the dependency and the corresponding
    # subfolder for the 'master' checkout
    repo_folder = test_directory.mkdir('links-01234')
    master_folder = repo_folder.mkdir('master')

    dependency = mock.Mock()
    dependency.name = 'links'
    dependency.major = 5
    latest_tag = '5.1.0'
    # The sources should contain the 'steinwurf' string, otherwise the
    # ExistingTagResolver will ignore them
    sources = ['https://gitlab.com/steinwurf/links.git']

    git_resolver = mock.Mock()
    git_resolver.resolve.return_value = master_folder.path()

    semver_selector = mock.Mock()
    semver_selector.select_tag.return_value = latest_tag

    tag_database = mock.Mock()
    tag_database.project_tags.return_value = ['5.1.0', '5.0.0']

    parent_folder = mock.Mock()
    parent_folder.parent_folder.return_value = repo_folder.path()

    resolver = ExistingTagResolver(ctx=ctx, dependency=dependency,
        semver_selector=semver_selector, tag_database=tag_database,
        parent_folder=parent_folder, sources=sources)

    # repo_folder is empty, so the resolver should return None
    path = resolver.resolve()
    assert path == None

    # Now we invoke the GitSemverResolver to get the latest tag
    git_semver_resolver = GitSemverResolver(git=git, git_resolver=git_resolver,
        ctx=ctx, semver_selector=semver_selector, dependency=dependency)

    path = git_semver_resolver.resolve()

    # The folder containing tag 5.1.0 should now exist
    assert repo_folder.contains_dir('5.1.0')
    latest_tag_folder = repo_folder.join('5.1.0')
    assert path == latest_tag_folder.path()

    # The ExistingTagResolver should find the latest tag in repo_folder
    path = resolver.resolve()
    assert path == latest_tag_folder.path()
