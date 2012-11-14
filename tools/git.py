#! /usr/bin/env python
# encoding: utf-8

import os

from waflib.Configure import conf
from waflib import Context
from waflib import Utils
from waflib import Errors

try:
    import _winreg
except:
    try:
        import winreg as _winreg
    except:
        _winreg = None


def find_in_winreg():
    """
    Look in the windows reg database for traces
    of the msysgit installer
    :return: the path to the git folder if found otherwise an empty string
    """

    reg_value = reg_type = None

    try:
        reg_key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE,
                                  'SOFTWARE\\Wow6432node\\Microsoft'
                                  '\\Windows\\CurrentVersion\\'
                                  'Uninstall\\Git_is1')

        (reg_value, reg_type) = _winreg.QueryValueEx(reg_key,
                                                     'InstallLocation')


    except WindowsError as e:

        try:
            reg_key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE,
                                      'SOFTWARE\\Microsoft'
                                      '\\Windows\\CurrentVersion\\'
                                      'Uninstall\\Git_is1')

            (reg_value, reg_type) = _winreg.QueryValueEx(reg_key,
                                                         'InstallLocation')

        except WindowsError:
            pass

    if reg_type == _winreg.REG_SZ:
        return str(reg_value)
    else:
        return ''


def find_git_win32(conf):
    """
    Attempt to find the git binary on windows
    :param conf: a Waf ConfigurationContext
    """
    path = find_in_winreg()

    if path:
        path_list = [path, os.path.join(path, 'bin')]
        conf.find_program('git', path_list = path_list)
    else:
        conf.find_program('git')


def configure(conf):
    """
    Attempts to locate the git binary
    :param conf: a Waf ConfigurationContext
    """

    if Utils.is_win32:
        find_git_win32(conf)
    else:
        conf.find_program('git')


@conf
def git_cmd_and_log(ctx, cmd, **kw):
    """
    Runs a git command
    """

    cmd = Utils.to_list(cmd)

    if not 'GIT' in ctx.env:
        raise Errors.WafError('The git program must be available')

    git_cmd = ctx.env['GIT']

    cmd = [git_cmd] + cmd

    return ctx.cmd_and_log(cmd, **kw)


@conf
def git_tags(ctx, **kw):
    """
    Runs 'git tag -l' and retuns the tags
    :param ctx: Waf Context
    """
    o = git_cmd_and_log(ctx, 'tag -l', **kw)
    tags = o.split('\n')
    return [t for t in tags if t != '']


@conf
def git_checkout(ctx, branch, **kw):
    """
    Runs 'git checkout branch'
    """
    git_cmd_and_log(ctx, 'checkout ' + branch, **kw)


@conf
def git_pull(ctx, **kw):
    """
    Runs 'git pull'
    """
    git_cmd_and_log(ctx, 'pull', **kw)


@conf
def git_branch(ctx, **kw):
    """
    Runs 'git branch' and returns the current branch and a list of
    additional branches
    """

    o = git_cmd_and_log(ctx, 'branch', **kw)

    branch = o.split('\n')
    branch = [b for b in branch if b != '']

    current = ''
    others = []

    for b in branch:
        if b.startswith('*'):
            current = b[1:].strip()
        else:
            others.append(b)

    if current == '':
        ctx.fatal('Failed to locate current branch')

    return current, others


@conf
def git_has_submodules(ctx, repository_dir):
    """
    Returns true if the repository contains the .gitmodules file
    :param repository_dir: directory to check for git submodules
    """
    return os.path.isfile(os.path.join(repository_dir, '.gitmodules'))


@conf
def git_submodule_init(ctx, **kw):
    """
    Runs 'git submodule init'
    """
    git_cmd_and_log(ctx, 'submodule init', **kw)


@conf
def git_submodule_update(ctx, **kw):
    """
    Runs 'git submodule update'
    """
    git_cmd_and_log(ctx, 'submodule update', **kw)


@conf
def git_submodule_sync(ctx, **kw):
    """
    Runs 'git submodule sync'
    """
    git_cmd_and_log(ctx, 'submodule sync', **kw)


@conf
def git_clone(ctx, source, destination, **kw):
    """
    Clone a repository
    """
    git_cmd_and_log(ctx, 'clone '+source+' '+destination, **kw)


@conf
def git_local_clone(ctx, source, destination, **kw):
    """
    Clone a repository
    """

    if Utils.is_win32:
        ctx.to_log('git local clone: fallback to git clone on win32')
        git_clone(ctx, source, destination)

    else:
        git_cmd_and_log(ctx, 'clone -l '+source+' '+destination, **kw)





