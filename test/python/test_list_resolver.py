import mock

from wurf.list_resolver import ListResolver


def test_list_resolver():

    # Define two resolvers that return a path
    resolver1 = mock.Mock()
    resolver1.resolve = mock.Mock(return_value='path1')

    resolver2 = mock.Mock()
    resolver2.resolve = mock.Mock(return_value='path2')

    resolver = ListResolver(resolvers=[resolver1, resolver2])

    ret = resolver.resolve()

    assert ret == 'path1'

    # Make the first resolver return None
    resolver1.resolve = mock.Mock(return_value=None)

    ret = resolver.resolve()

    assert ret == 'path2'

    # Make the second resolver also return None
    resolver2.resolve = mock.Mock(return_value=None)

    ret = resolver.resolve()

    assert ret is None
