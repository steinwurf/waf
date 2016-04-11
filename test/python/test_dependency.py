import os
import sys
import subprocess
import glob
import time
import mock
import pytest
import json

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
#
# The below unit tests will test the functionality of the WurfDependency class.
#
# Few things to note:
#
# 1. We do not check the content of start_msg, end_msg and calls to
# ctx.to_log since we don't want the unit tests to break if you simply
# change the content of the string being printed.
#
# 2. In the tests below we use pytest decorators to paramerterize them. So
# when you see the following:
#
#    @pytest.mark.parametrize("recurse", [True, False])
#    @pytest.mark.parametrize("optional", [True, False])
#    def test_some_function(test_directory, recurse, optional):
#        pass
#
# It means that the test_something will be called four times
#
#    {recurse=True, optional=True},{recurse=True, optional=False},
#    {recurse=False, optional=True},{recurse=False, optional=False}
#
# Read more about pytest paramerterize here:
# https://pytest.org/latest/parametrize.html


@pytest.mark.parametrize("recurse", [True, False])
@pytest.mark.parametrize("optional", [True, False])
def test_wurf_dependency_resolve_success(test_directory, recurse, optional):
    # 1. resolve success recurse=True|False, optional=True|False

    resolver = mock.Mock()
    resolver.hash.return_value='h4sh'
    resolver.resolve.return_value='dummy_path'

    d = WurfDependency('abc', resolver, recurse=recurse, optional=optional)

    ctx = mock.Mock()
    ctx.cmd = 'resolve'
    ctx.bundle_path.return_value=test_directory.path()

    d.resolve(ctx)

    resolver_path = os.path.join(test_directory.path(), 'abc-h4sh')
    resolver.resolve.assert_called_once_with(ctx, resolver_path)

    assert d.path == 'dummy_path'
    assert os.path.exists(resolver_path)
    assert ctx.start_msg.call_count == 1

    assert ctx.end_msg.call_count == 1

    # Check whether ctx.recurse() was called
    if recurse:
        ctx.recurse.assert_called_once_with('dummy_path')
    else:
        assert not ctx.recurse.called

@pytest.mark.parametrize("recurse", [True, False])
@pytest.mark.parametrize("optional", [True, False])
def test_wurf_dependency_resolve_failure(test_directory, recurse, optional):
    # 1. resolve failure recurse=False, optional=False

    resolver = mock.Mock()
    resolver.hash.return_value='h4sh'

    # Calling resolve will raise an exception
    resolver.resolve.side_effect=Exception('Boom!')

    d = WurfDependency('abc', resolver, recurse=recurse, optional=optional)

    ctx = mock.Mock()
    ctx.cmd = 'resolve'
    ctx.bundle_path.return_value=test_directory.path()
    ctx.fatal.side_effect=Exception()

    try:
        d.resolve(ctx)
    except:
        # If the dependency is not optional we should see an exception now
        assert not optional

    else:
        # We do not expect an exception if the dependency is optional
        assert optional
        assert ctx.start_msg.call_count == 1
        assert ctx.end_msg.call_count == 1

    resolver_path = os.path.join(test_directory.path(), 'abc-h4sh')
    resolver.resolve.assert_called_once_with(ctx, resolver_path)

    assert d.path is None
    assert os.path.exists(resolver_path)

    # Check recurse is never called since we don't have a path - resolved
    # failed ;)
    assert not ctx.recurse.called


@pytest.mark.parametrize("recurse", [True, False])
@pytest.mark.parametrize("optional", [True, False])
def test_wurf_dependency_store_has_path(test_directory, recurse, optional):
    """Tests store(...) function of WurfDependency when a path is available."""

    resolver = mock.Mock()
    resolver.hash.return_value='h4sh'

    d = WurfDependency('abc', resolver, recurse=recurse, optional=optional)

    build_directory = test_directory.mkdir('build')

    ctx = mock.Mock()
    ctx.bundle_config_path.return_value = build_directory.path()

    abc_directory = test_directory.mkdir('abc')
    d.path = abc_directory.path()

    d.store(ctx)

    json_path = os.path.join(build_directory.path(), 'abc.resolve.json')
    assert os.path.isfile(json_path)

    # Lets read back the stored json file and see that every things works
    with open(json_path, 'r') as json_file:
        data = json.load(json_file)

    assert data['optional'] == optional
    assert data['recurse'] == recurse
    assert data['path'] == abc_directory.path()
    assert data['resolver_hash'] == 'h4sh'

@pytest.mark.parametrize("recurse", [True, False])
@pytest.mark.parametrize("optional", [True, False])
def test_wurf_dependency_store_no_path(test_directory, recurse, optional):
    """ Tests the store(...) function of WurfDependency when no path is available.

    When there is no path we expect an assert to fire.
    """
    resolver = mock.Mock()
    ctx = mock.Mock()
    ctx.fatal.side_effect = Exception()

    d = WurfDependency('abc', resolver, recurse=recurse, optional=optional)

    with pytest.raises(Exception):
        d.store(ctx)


@pytest.mark.parametrize("recurse", [True, False])
@pytest.mark.parametrize("optional", [True, False])
def test_wurf_dependency_load_no_path(test_directory, recurse, optional):
    """ Tests the load(...) function of WurfDependency with missing load path.

    The path where the dependency configuration should be stored is missing.
    """
    resolver = mock.Mock()
    ctx = mock.Mock()
    ctx.bundle_config_path.return_value = os.path.join(
        test_directory.path(), 'nonexisting')
    ctx.fatal.side_effect = Exception()

    d = WurfDependency('abc', mock.Mock(), recurse=recurse, optional=optional)

    with pytest.raises(Exception):
        d.load(ctx)


@pytest.mark.parametrize("recurse", [True, False])
@pytest.mark.parametrize("optional", [True, False])
def test_wurf_dependency_load_with_dependency_path(test_directory, recurse,
                                                   optional):
    """Tests the load(...) function of WurfDependency which already has a path.

    It is a programming error to load a dependency twice or to load after
    reolve.
    """
    d = WurfDependency('abc', mock.Mock(), recurse=recurse, optional=optional)
    d.path = test_directory.path()

    with pytest.raises(AssertionError):
        d.load(path)


@pytest.mark.parametrize("recurse", [True, False])
@pytest.mark.parametrize("optional", [True, False])
def test_wurf_dependency_load_with_dependency_path(test_directory, recurse,
                                                   optional):
    """If we try to load from a path where the config file does not exist
    it should raise an exception.
    """
    d = WurfDependency('abc', mock.Mock(), recurse=recurse, optional=optional)

    with pytest.raises(Exception):
        d.load(test_directory)


# @pytest.mark.parametrize("recurse", [True, False])
# @pytest.mark.parametrize("optional", [True, False])
# def test_wurf_dependency_load_with_dependency_path(test_directory):
#     """If we try to load from a path where the config file does not exist
#     it should raise an exception.
#     """
#     d = WurfDependency('abc', mock.Mock(), recurse=recurse, optional=optional)

    # test_directory.write_file(

    # with pytest.raises(Exception)
    #     d.load(test_directory)
