import mock

from wurf.git import Git


def test_git_version():

    ctx = mock.Mock()
    ctx.cmd_and_log.return_value = "git version 1.8.1.msysgit.1"

    git = Git("/bin/git_binary", ctx)

    assert git.version() == (1, 8, 1, 1)
    ctx.cmd_and_log.assert_called_once_with(["/bin/git_binary", "version"])

    ctx.cmd_and_log.return_value = "git version 2.7.4"

    assert git.version() == (2, 7, 4)


def test_git_current_commit():

    ctx = mock.Mock()
    ctx.cmd_and_log.return_value = """044d59505f3b63645c7fb7dec145154b8e518086"""

    git = Git("/bin/git_binary", ctx)

    assert git.current_commit(cwd="/tmp") == "044d59505f3b63645c7fb7dec145154b8e518086"
    ctx.cmd_and_log.assert_called_once_with(
        ["/bin/git_binary", "rev-parse", "HEAD"], cwd="/tmp"
    )


def test_git_current_tag(testdirectory):

    ctx = mock.Mock()
    ctx.cmd_and_log.side_effect = ["044d59505f3b63645c7fb7dec145154b8e518086", "2.0.0"]

    git = Git("/bin/git_binary", ctx)

    assert git.current_tag(cwd="/tmp") == "2.0.0"

    print(ctx.cmd_and_log.call_args_list)

    ctx.cmd_and_log.assert_has_calls(
        [
            mock.call(["/bin/git_binary", "rev-parse", "HEAD"], cwd="/tmp"),
            mock.call(
                [
                    "/bin/git_binary",
                    "tag",
                    "--points-at",
                    "044d59505f3b63645c7fb7dec145154b8e518086",
                ],
                cwd="/tmp",
            ),
        ]
    )


def test_git_clone():

    ctx = mock.Mock()
    git = Git("/bin/git_binary", ctx)

    git.clone(
        repository="https://github.com/repo.git", directory="/tmp/repo2", cwd="/tmp"
    )

    ctx.cmd_and_log.assert_called_once_with(
        ["/bin/git_binary", "clone", "https://github.com/repo.git", "/tmp/repo2"],
        cwd="/tmp",
    )


def test_git_pull():

    ctx = mock.Mock()
    git = Git("/bin/git_binary", ctx)

    git.pull(cwd="/tmp")

    ctx.cmd_and_log.assert_called_once_with(["/bin/git_binary", "pull"], cwd="/tmp")


def test_git_has_submodules(testdirectory):

    ctx = mock.Mock()
    git = Git("/bin/git_binary", ctx)

    cwd = testdirectory.path()

    assert git.has_submodules(cwd=cwd) is False

    testdirectory.write_text(".gitmodules", "not important", encoding="utf-8")

    assert git.has_submodules(cwd=cwd) is True


def test_git_sync_submodules():

    ctx = mock.Mock()
    git = Git("/bin/git_binary", ctx)

    git.sync_submodules(cwd="/tmp")

    ctx.cmd_and_log.assert_called_once_with(
        ["/bin/git_binary", "submodule", "sync"], cwd="/tmp"
    )


def test_git_init_submodules():

    ctx = mock.Mock()
    git = Git("/bin/git_binary", ctx)

    git.init_submodules(cwd="/tmp")

    ctx.cmd_and_log.assert_called_once_with(
        ["/bin/git_binary", "submodule", "init"], cwd="/tmp"
    )


def test_git_update_submodules():

    ctx = mock.Mock()
    git = Git("/bin/git_binary", ctx)

    git.update_submodules(cwd="/tmp")

    ctx.cmd_and_log.assert_called_once_with(
        ["/bin/git_binary", "submodule", "update"], cwd="/tmp"
    )


def test_git_pull_submodules(testdirectory):

    ctx = mock.Mock()
    git = Git("/bin/git_binary", ctx)

    cwd = testdirectory.path()

    git.pull_submodules(cwd=cwd)

    ctx.cmd_and_log.assert_not_called()

    testdirectory.write_text(".gitmodules", "not important", encoding="utf-8")

    def check_command(cmd, cwd):
        expected_cmd = check_command.commands.pop(0)
        assert expected_cmd == cmd[2]

    check_command.commands = ["sync", "init", "update"]

    ctx.cmd_and_log.side_effect = check_command

    git.pull_submodules(cwd=cwd)
