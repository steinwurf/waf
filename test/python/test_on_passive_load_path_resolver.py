import mock

from wurf.on_passive_load_path_resolver import OnPassiveLoadPathResolver


def test_on_passive_load_path_resolver(testdirectory):
    # @todo add tests
    dependency = mock.Mock()
    resolve_config_path = testdirectory.path()

    resolve = OnPassiveLoadPathResolver(
        dependency=dependency,
        resolve_config_path=resolve_config_path)

    assert resolve
