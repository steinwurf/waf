import mock

from wurf.try_resolver import TryResolver
from wurf.error import Error


def test_try_resolver(testdirectory):

    ctx = mock.Mock()
    dependency = mock.Mock()
    dependency.name = 'foo'
    dependency.__contains__ = mock.Mock()
    dependency.__contains__.return_value = False

    # TryResolver needs a resolver that returns a valid path
    resolver1 = mock.Mock()
    resolver1.resolve = mock.Mock(return_value=testdirectory.path())

    resolver = TryResolver(resolver=resolver1, ctx=ctx, dependency=dependency)

    path = resolver.resolve()

    assert path == testdirectory.path()

    # Make resolver1 fail with an Error
    def raise_error():
        raise Error('random error')

    resolver1.resolve = mock.Mock(side_effect=raise_error)

    # TryResolver should just return with None
    path = resolver.resolve()

    assert path is None
