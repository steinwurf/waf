import os
import mock
import pytest

from wurf.post_resolve_run import PostResolveRun
from wurf.error import WurfError


def test_post_resolve_run(testdirectory):

    resolver_folder = testdirectory.mkdir('somefolder-01234')
    resolver = mock.Mock()
    resolver.resolve.return_value = resolver_folder.path()

    ctx = mock.Mock()
    run = "tar -xyz this.tar.gz"
    cwd = testdirectory.path()

    resolver = PostResolveRun(
        resolver=resolver, ctx=ctx, run=run, cwd=cwd)

    path = resolver.resolve()

    # The checkout path should now exist
    assert os.path.isdir(path)

    ctx.cmd_and_log.assert_called_once_with(cmd=run, cwd=path)


def test_post_resolve_run_failed(testdirectory):

    resolver_folder = testdirectory.mkdir('somefolder-01234')
    resolver = mock.Mock()
    resolver.resolve.return_value = resolver_folder.path()

    ctx = mock.Mock()
    ctx.cmd_and_log.side_effect = WurfError("Bang!")
    run = "tar -xyz this.tar.gz"
    cwd = testdirectory.path()

    resolver = PostResolveRun(
        resolver=resolver, ctx=ctx, run=run, cwd=cwd)

    with pytest.raises(WurfError):
        resolver.resolve()

    # The run-xxxx folder should be cleaned out
    assert not resolver_folder.contains_dir('run-*')
