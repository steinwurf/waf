import pytest
import mock

import wurf_git

def test_wurf_git_version():

    ctx = mock.Mock()
    ctx.cmd_and_log.return_value = 'git version 1.8.1.msysgit.1'

    git = wurf_git.Git('/bin/git_binary', ctx)

    assert(git.version() == (1,8,1,1))
    ctx.cmd_and_log.assert_called_once_with(['/bin/git_binary', 'version'])

    ctx.cmd_and_log.return_value = 'git version 2.7.4'

    assert(git.version() == (2,7,4))

def test_wurf_git_clone():

    ctx = mock.Mock()
    git = wurf_git.Git('/bin/git_binary', ctx)

    git.clone(repository='https://github.com/repo.git',
              directory='/tmp/repo2',
              cwd='/tmp')

    ctx.cmd_and_log.assert_called_once_with(
        ['/bin/git_binary','clone','https://github.com/repo.git','/tmp/repo2'],
        cwd='/tmp')

def test_wurf_git_pull():

    ctx = mock.Mock()
    git = wurf_git.Git('/bin/git_binary', ctx)

    git.pull(cwd='/tmp')

    ctx.cmd_and_log.assert_called_once_with(
        ['/bin/git_binary','pull'], cwd='/tmp')

def test_wurf_git_pull():

    ctx = mock.Mock()
    git = wurf_git.Git('/bin/git_binary', ctx)

    git.pull(cwd='/tmp')

    ctx.cmd_and_log.assert_called_once_with(
        ['/bin/git_binary','pull'], cwd='/tmp')

def test_wurf_git_has_submodules(test_directory):

    ctx = mock.Mock()
    git = wurf_git.Git('/bin/git_binary', ctx)

    cwd = test_directory.path()

    assert(git.has_submodules(cwd=cwd) == False)

    test_directory.write_file('.gitmodules', 'not important')

    assert(git.has_submodules(cwd=cwd) == True)
