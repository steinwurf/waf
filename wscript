#! /usr/bin/env python
# encoding: utf-8

import os

from waflib import Build

top = '.'

def resolve(ctx):

    ctx.add_git_semver_dependency(
        name='waf-tools',
        git_repository='github.com/steinwurf/waf-tools.git',
        major=3)

    ctx.add_git_commit_dependency(
        name='waf',
        git_repository='github.com/waf-project/waf.git',
        commit='waf-1.8.14',
        recursive_resolve=False)

    ctx.add_git_commit_dependency(
        name='python-semver',
        git_repository='github.com/k-bx/python-semver.git',
        commit='2.4.1',
        recursive_resolve=False)

def configure(conf):

    # Lets get rid of this load as well at some point
    conf.load('wurf_common_tools')

    # Ensure that the waf-light program is available in the in the
    # waf folder. This is used to build the waf binary.
    conf.find_program('waf-light',
        path_list=[conf.dependency_path('waf')])

    # Make sure we tox used for running unit tests
    conf.find_program('tox')

def build_waf_binary(tsk):
    """
    Task for building the waf binary.
    """

    # Get the working directory
    wd = getattr(tsk, 'cwd', None)

    # Get the absolute path to all the tools (passed as input to the task)
    tool_paths = [t.abspath() for t in tsk.inputs]
    tool_paths = ','.join(tool_paths)

    # The prelude option
    prelude = '\timport waflib.extras.wurf_entry_point'

    # Build the command to execute
    command = "python waf-light --make-waf --prelude='{}' --tools={}".format(
        prelude, tool_paths)

    return tsk.exec_command(command, cwd=wd)

def build(bld):

    # Waf checks that source files are available when we create the
    # different tasks. We can ask waf to lazily do this because the waf
    # binary is not created until after we run the waf-light build
    # step. This is manipulated using the post_mode.
    bld.post_mode = Build.POST_LAZY

    # We need to invoke the waf-light from within the third_party/waf
    # folder as waf-light will look for wscript in the folder where the
    # executable was started - so we need to start it from the right
    # folder. Using cwd we can make sure the python process is lauched in
    # the right directory.
    tools = bld.path.ant_glob('tools/*.py')
    tools += [bld.root.find_node(
        os.path.join(bld.dependency_path('python-semver'), 'semver.py'))]

    bld(rule=build_waf_binary,
        source=tools,
        cwd=bld.dependency_path('waf'))

    bld.add_group()

    # Copy the waf binary to build directory
    bld(features='subst',
        source=bld.root.find_node(
            os.path.join(bld.dependency_path('waf'), 'waf')),
        target=bld.bldnode.make_node('waf'),
        is_copy=True)

    # Make a build group will ensure that
    bld.add_group()


    # Invoke tox to run all the pure Python unit tests. Tox creates
    # virtualenvs for different setups and runs unit tests in them. See the
    # tox.ini to see the configuration used and see
    # https://tox.readthedocs.org/ for more information about tox.
    bld(rule='tox')
