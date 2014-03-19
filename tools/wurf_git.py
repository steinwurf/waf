#! /usr/bin/env python
# encoding: utf-8

import os
import re

from waflib.Configure import conf
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

    except WindowsError:

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
        conf.find_program('git', path_list=path_list)
    else:
        conf.find_program('git')


def options(opt):
    """
    Add option to specify git protocol
    Options are shown when ./waf -h is invoked
    :param opt: the Waf OptionsContext
    """
    opt.add_option_group('git options')


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
def git_check_minimum_version(conf, minimum):
    """
    Checks the minimum version of git
    :param ctx: Waf context
    :param args: The required minimum version as a tuple
    """
    version = conf.git_version()
    if version[:3] < minimum:
        conf.fatal("Git version not supported: {0}, "
                   "required minimum version: {1}"
                   .format(version, minimum))


@conf
def git_cmd_and_log(ctx, args, **kw):
    """
    Runs a git command
    :param ctx: Waf Context
    :param args: Program arguments as a list
    """

    if not 'GIT' in ctx.env:
        raise Errors.WafError('The git program must be available')

    git_cmd = ctx.env['GIT']

    args = [git_cmd] + args

    return ctx.cmd_and_log(args, **kw)


@conf
def git_version(ctx, **kw):
    """
    Runs 'git tag -l' and returns the version information as a tuple
    :param ctx: Waf Context
    """
    output = git_cmd_and_log(ctx, ['version'], **kw).strip()
    # The output looks like "git version 1.8.1.msysgit.1"
    # we just extract the integers
    int_list = [int(s) for s in re.findall('\\d+', output)]
    return tuple(int_list)


@conf
def git_tags(ctx, **kw):
    """
    Runs 'git tag -l' and returns the tags
    :param ctx: Waf Context
    """
    o = git_cmd_and_log(ctx, ['tag', '-l'], **kw)
    tags = o.split('\n')
    return [t for t in tags if t != '']


@conf
def git_checkout(ctx, branch, **kw):
    """
    Runs 'git checkout branch'
    """
    git_cmd_and_log(ctx, ['checkout', branch], **kw)


@conf
def git_pull(ctx, **kw):
    """
    Runs 'git pull'
    """
    git_cmd_and_log(ctx, ['pull'], **kw)


@conf
def git_config(ctx, args, **kw):
    """
    Runs 'git config args' and returns the output
    :param ctx: Waf Context
    """
    output = git_cmd_and_log(ctx, ['config'] + args, **kw)
    return output.strip()


@conf
def git_branch(ctx, **kw):
    """
    Runs 'git branch' and returns the current branch and a list of
    additional branches
    """

    o = git_cmd_and_log(ctx, ['branch'], **kw)

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
    git_cmd_and_log(ctx, ['submodule', 'init'], **kw)


@conf
def git_submodule_update(ctx, **kw):
    """
    Runs 'git submodule update'
    """
    git_cmd_and_log(ctx, ['submodule', 'update'], **kw)


@conf
def git_submodule_sync(ctx, **kw):
    """
    Runs 'git submodule sync'
    """
    git_cmd_and_log(ctx, ['submodule', 'sync'], **kw)


@conf
def git_clone(ctx, source, destination, **kw):
    """
    Clone a repository
    """
    git_cmd_and_log(ctx, ['clone', source, destination], **kw)


@conf
def git_local_clone(ctx, source, destination, **kw):
    """
    Clone a repository
    """

# if Utils.is_win32:
##        ctx.to_log('git local clone: fallback to git clone on win32')
##        git_clone(ctx, source, destination)
# else:

    # We have to disable hard-links since the do not work on the
    # AFS file system. We may later revisit this.
    git_cmd_and_log(
        ctx, ['clone', '-l', '--no-hardlinks', source, destination], **kw)
