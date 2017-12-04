import os
import mock

from wurf.post_resolve_run import PostResolveRun


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
