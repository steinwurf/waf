import pytest
import mock

from wurf.path_resolver import PathResolver
from wurf.error import DependencyError


def test_path_resolver_invalid_path():

    dependency = mock.Mock()
    dependency.name = 'foo'

    path = '/tmp/this_should_not_exist'

    resolver = PathResolver(dependency=dependency, path=path)

    # A DependencyError should be raised for a non-existent path
    with pytest.raises(DependencyError):
        resolver.resolve()


def test_path_resolver_valid_path(test_directory):

    dependency = mock.Mock()
    dependency.name = 'foo'

    path = test_directory.path()

    resolver = PathResolver(dependency=dependency, path=path)

    ret = resolver.resolve()

    assert ret == path
