import pytest
import mock

from wurf.check_optional_resolver import CheckOptionalResolver
from wurf.error import TopLevelError


def test_check_optional_resolver():

    dependency = mock.Mock()
    dependency.name = 'foo'
    dependency.optional = True

    # Define a resolver that returns a path
    resolver1 = mock.Mock()
    resolver1.resolve = mock.Mock(return_value='path1')

    resolver = CheckOptionalResolver(resolver=resolver1,
        dependency=dependency)

    ret = resolver.resolve()

    assert ret == 'path1'

    # Make resolver1 return None
    resolver1.resolve = mock.Mock(return_value=None)

    # The dependency is optional, so this should not raise a TopLevelError
    ret = resolver.resolve()

    assert ret == None

    # Make the dependency non-optional
    dependency.optional = False

    # A TopLevelError should be raised for a missing path and a non-optional
    # dependency
    with pytest.raises(TopLevelError):
        resolver.resolve()
