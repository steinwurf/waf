import pytest
import mock

from wurf.git import Git


def test_wurf_git_version():

    ctx = mock.Mock()
    ctx.cmd_and_log.return_value = 'git version 1.8.1.msysgit.1'

    git = Git('/bin/git_binary', ctx)

    assert(git.version() == (1,8,1,1))
    ctx.cmd_and_log.assert_called_once_with(['/bin/git_binary', 'version'])

    ctx.cmd_and_log.return_value = 'git version 2.7.4'

    assert(git.version() == (2,7,4))

def test_wurf_git_current_commit():

    ctx = mock.Mock()
    ctx.cmd_and_log.return_value ="""commit 044d59505f3b63645c7fb7dec145154b8e518086
Author: Morten V. Pedersen <morten@mortenvp.com>
Date:   Thu Mar 9 20:35:37 2017 +0100"""

    git = Git('/bin/git_binary', ctx)

    assert git.current_commit(cwd='/tmp') == "044d59505f3b63645c7fb7dec145154b8e518086"
    ctx.cmd_and_log.assert_called_once_with(
        ['/bin/git_binary', 'log', '-1'], cwd='/tmp')

    ctx.cmd_and_log.return_value = 'git version 2.7.4'

def test_wurf_git_clone():

    ctx = mock.Mock()
    git = Git('/bin/git_binary', ctx)

    git.clone(repository='https://github.com/repo.git',
              directory='/tmp/repo2',
              cwd='/tmp')

    ctx.cmd_and_log.assert_called_once_with(
        ['/bin/git_binary','clone','https://github.com/repo.git','/tmp/repo2'],
        cwd='/tmp')

def test_wurf_git_pull():

    ctx = mock.Mock()
    git = Git('/bin/git_binary', ctx)

    git.pull(cwd='/tmp')

    ctx.cmd_and_log.assert_called_once_with(
        ['/bin/git_binary','pull'], cwd='/tmp')

def test_wurf_git_has_submodules(test_directory):

    ctx = mock.Mock()
    git = Git('/bin/git_binary', ctx)

    cwd = test_directory.path()

    assert(git.has_submodules(cwd=cwd) == False)

    test_directory.write_file('.gitmodules', 'not important')

    assert(git.has_submodules(cwd=cwd) == True)

def test_wurf_git_sync_submodules():

    ctx = mock.Mock()
    git = Git('/bin/git_binary', ctx)

    git.sync_submodules(cwd='/tmp')

    ctx.cmd_and_log.assert_called_once_with(
        ['/bin/git_binary','submodule','sync'], cwd='/tmp')

def test_wurf_git_init_submodules():

    ctx = mock.Mock()
    git = Git('/bin/git_binary', ctx)

    git.init_submodules(cwd='/tmp')

    ctx.cmd_and_log.assert_called_once_with(
        ['/bin/git_binary','submodule','init'], cwd='/tmp')

def test_wurf_git_update_submodules():

    ctx = mock.Mock()
    git = Git('/bin/git_binary', ctx)

    git.update_submodules(cwd='/tmp')

    ctx.cmd_and_log.assert_called_once_with(
        ['/bin/git_binary','submodule','update'], cwd='/tmp')

def test_wurf_git_pull_submodules(test_directory):

    ctx = mock.Mock()
    git = Git('/bin/git_binary', ctx)

    cwd = test_directory.path()

    git.pull_submodules(cwd=cwd)

    ctx.cmd_and_log.assert_not_called()

    test_directory.write_file('.gitmodules', 'not important')

    def check_command(cmd, cwd):
        expected_cmd = check_command.commands.pop(0)
        assert(expected_cmd == cmd[2])

    check_command.commands = ['sync', 'init', 'update']

    ctx.cmd_and_log.side_effect = check_command

    git.pull_submodules(cwd=cwd)
