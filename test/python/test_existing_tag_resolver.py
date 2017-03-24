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
    dependency.git_tag = '5.1.0'
    dependency.__contains__ = mock.Mock()
    dependency.__contains__.return_value = True
    latest_tag = '5.1.0'

    cwd = test_directory.mkdir('cwd')
    resolve_path = test_directory.mkdir('resolve_path')

    semver_selector = mock.Mock()
    semver_selector.select_tag.return_value = latest_tag

    tag_database = mock.Mock()
    tag_database.project_tags.return_value = ['5.1.0', '5.0.0']

    semver_resolver = mock.Mock()
    semver_resolver.resolve.return_value = resolve_path.path()

    # Run without any tags file

    resolver = ExistingTagResolver(ctx=ctx, dependency=dependency,
        semver_selector=semver_selector, tag_database=tag_database,
        resolver=semver_resolver, cwd=cwd.path())

    path = resolver.resolve()

    assert path == resolve_path.path()

    assert cwd.contains_file('foo.tags.json')

    # Run with a tags file, we will not use the resolver

    resolver = ExistingTagResolver(ctx=ctx, dependency=dependency,
        semver_selector=semver_selector, tag_database=tag_database,
        resolver=None, cwd=cwd.path())

    path = resolver.resolve()

    assert path == resolve_path.path()

    # Remove the resolve path and check we fallback to resolver

    resolve_path.rmdir()
    resolve_path = test_directory.mkdir('resolve_path2')
    semver_resolver.resolve.return_value = resolve_path.path()

    resolver = ExistingTagResolver(ctx=ctx, dependency=dependency,
        semver_selector=semver_selector, tag_database=tag_database,
        resolver=semver_resolver, cwd=cwd.path())

    path = resolver.resolve()

    assert path == resolve_path.path()
