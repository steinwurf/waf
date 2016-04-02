import os
import sys
import subprocess
import glob
import time
import mock
import pytest

from wurf_dependency import WurfDependency

# Lets enumerate the test cases for resolve(...)
#
# 1. resolve success recurse=False, optional=True|False
# 2. resolve success recurse=True, optional=True|False
#
# In the above when resolve is a success it does not matter whether
# optional is True of False it should give the same outcome

# 5. resolvs failure recurse=False|True, optional=False
# 6. resolve failure recurse=False|True, optional=False


@pytest.mark.parametrize("recurse", [True, False])
@pytest.mark.parametrize("optional", [True, False])
def test_wurf_dependency_resolve_success(test_directory, recurse, optional):
    # 1. resolve success recurse=True|False, optional=True|False

    resolver = mock.Mock()
    resolver.hash = mock.Mock(return_value='h4sh')
    resolver.resolve = mock.Mock(return_value='dummy_path')

    d = WurfDependency('abc', resolver, recurse=recurse, optional=optional)

    ctx = mock.Mock()
    ctx.cmd = 'resolve'
    ctx.dependency_path = mock.Mock(return_value=test_directory.path())

    d.resolve(ctx)

    resolver_path = os.path.join(test_directory.path(), 'abc-h4sh')
    resolver.resolve.assert_called_once_with(ctx, resolver_path)
    assert d.path == 'dummy_path'
    # assert os.path.exists(os.path.join(test_directory.path(), 'abc-hash'))
    # assert ctx.start_msg.call_count == 1
    #
    # assert ctx.end_msg.call_count == 1

    # # Check whether ctx.recurse() was called
    # if recurse:
    #     assert ctx.recurse.called_once_with('dummy_path')
    # else:
    #     assert not ctx.recurse.called

@pytest.mark.parametrize("recurse", [True, False])
@pytest.mark.parametrize("optional", [True, False])
def test_wurf_dependency_resolve_failure(test_directory, recurse, optional):
    # 1. resolve success recurse=False, optional=False

    resolver = mock.Mock()
    resolver.hash = mock.Mock(return_value='hash')

    # Calling resolve will raise an exception
    resolver.resolve = mock.Mock(side_effect=Exception('Boom!'))

    d = WurfDependency('abc', resolver, recurse=recurse, optional=optional)

    ctx = mock.Mock()
    ctx.cmd = 'resolve'
    ctx.dependency_path = mock.Mock(return_value=test_directory.path())

    d.resolve(ctx)

    assert d.path is None
    assert os.path.exists(os.path.join(test_directory.path(), 'abc-hash'))
    assert ctx.start_msg.call_count == 1
    assert resolver.resolve.called_once_with(ctx)

    # If the dependency is optional we just call end_msg function otherwise
    # we raise a fatal error by calling ctx.fatal
    if optional:
        assert ctx.end_msg.call_count == 1
        assert not ctx.fatal.called
    else:
        assert not ctx.end_msg.called
        assert ctx.fatal.call_count == 1

    # Check recurse is never called since we don't have a path - resolved
    # failed ;)
    assert not ctx.recurse.called


# @pytest.mark.parametrize("recurse", [True, False])
# @pytest.mark.parametrize("optional", [True, False])
# def test_wurf_dependency_store(test_directory, recurse, optional):

#     resolver = mock.Mock()
#     resolver.hash = mock.Mock(return_value='hash')
#     resolver.resolve = mock.Mock(return_value='dummy_path')

#     d = WurfDependency('abc', resolver, recurse=recurse, optional=optional)
