import mock

from wurf.existing_tag_resolver import ExistingTagResolver


def test_existing_tag_resolver(testdirectory):
    ctx = mock.Mock()
    git = mock.Mock()

    dependency = mock.Mock()
    dependency.name = "foo"
    dependency.major = 5
    dependency.git_tag = "5.1.0"
    dependency.__contains__ = mock.Mock()
    dependency.__contains__.return_value = True
    latest_tag = "5.1.0"

    cwd = testdirectory.mkdir("cwd")
    resolve_path = testdirectory.mkdir("resolve_path")

    semver_selector = mock.Mock()
    semver_selector.select_tag.return_value = latest_tag

    tag_database = mock.Mock()
    tag_database.project_tags.return_value = ["5.1.0", "5.0.0"]

    semver_resolver = mock.Mock()
    semver_resolver.resolve.return_value = resolve_path.path()

    # Run without any tags file
    resolver = ExistingTagResolver(
        ctx=ctx,
        git=git,
        dependency=dependency,
        semver_selector=semver_selector,
        tag_database=tag_database,
        resolver=semver_resolver,
        cwd=cwd.path(),
    )

    path = resolver.resolve()
    # The path is returned by the semver_resolver and a tag file is created
    semver_resolver.resolve.assert_called_once()
    assert path == resolve_path.path()
    assert cwd.contains_file("foo.tags.json")

    semver_resolver.reset_mock()

    # Run with a tags file, we will not use the semver_resolver
    resolver = ExistingTagResolver(
        ctx=ctx,
        git=git,
        dependency=dependency,
        semver_selector=semver_selector,
        tag_database=tag_database,
        resolver=None,
        cwd=cwd.path(),
    )

    path = resolver.resolve()
    assert semver_resolver.resolve.called is False
    assert path == resolve_path.path()

    # Remove the resolve path and check that we fallback to semver_resolver
    resolve_path.rmdir()
    resolve_path = testdirectory.mkdir("resolve_path2")
    semver_resolver.resolve.return_value = resolve_path.path()

    resolver = ExistingTagResolver(
        ctx=ctx,
        git=git,
        dependency=dependency,
        semver_selector=semver_selector,
        tag_database=tag_database,
        resolver=semver_resolver,
        cwd=cwd.path(),
    )

    path = resolver.resolve()
    semver_resolver.resolve.assert_called_once()
    assert path == resolve_path.path()
