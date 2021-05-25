import mock

from wurf.on_active_store_path_resolver import OnActiveStorePathResolver


def test_on_active_store_path_resolver(testdirectory):
    # @todo add tests
    resolver = mock.Mock()
    dependency = mock.Mock()
    resolve_config_path = testdirectory.path()

    resolve = OnActiveStorePathResolver(
        resolver=resolver,
        dependency=dependency,
        resolve_config_path=resolve_config_path,
    )

    assert resolve
