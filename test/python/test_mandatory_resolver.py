import pytest
import mock

from wurf.mandatory_resolver import MandatoryResolver
from wurf.error import TopLevelError


def test_mandatory_resolver():

    dependency = mock.Mock()
    dependency.name = "foo"

    # Define a resolver that returns a path
    resolver1 = mock.Mock()
    resolver1.resolve = mock.Mock(return_value="path1")

    resolver = MandatoryResolver(
        resolver=resolver1, msg="User message", dependency=dependency
    )

    ret = resolver.resolve()

    assert ret == "path1"

    # Make resolver1 return None
    resolver1.resolve = mock.Mock(return_value=None)

    # A TopLevelError should be raised for a missing path
    with pytest.raises(TopLevelError):
        resolver.resolve()
