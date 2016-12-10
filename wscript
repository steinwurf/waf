#! /usr/bin/env python
# encoding: utf-8

import os

from waflib import Build

top = '.'

def resolve(ctx):


    # ctx.add_git_semver_dependency(
        # name='waf-tools',
        # git_repository='github.com/steinwurf/waf-tools.git',
        # major=3)
    return
    ctx.add_dependency(
        name='waf',
        recurse=False,
        optional=False,
        resolver='git',
        method='checkout',
        checkout='waf-1.9.5',
        sources=['github.com/waf-project/waf.git'])

    # ctx.add_git_commit_dependency(
        # name='python-semver',
        # git_repository='github.com/k-bx/python-semver.git',
        # commit='2.4.1',
        # recursive_resolve=False)

def configure(conf):

    # Lets get rid of this load as well at some point
    #conf.load('wurf_common_tools')

    # Ensure that the waf-light program is available in the in the
    # waf folder. This is used to build the waf binary.
    #conf.find_program('waf-light',
    #    path_list=[conf.dependency_path('waf')])

    # Make sure we tox used for running unit tests
    conf.find_program('tox')

def build_waf_binary(tsk):
    """
    Task for building the waf binary.
    """

    # Get the working directory
    wd = getattr(tsk, 'cwd', None)

    # Tools dir
    tools_dir = getattr(tsk.generator, 'tools_dir', None)
    tools_dir = [os.path.abspath(os.path.expanduser(d)) for d in tools_dir]
    print("tools_dir {}".format(tools_dir))

    # Get the absolute path to all the tools (passed as input to the task)
    tool_paths = [t.abspath() for t in tsk.inputs] + tools_dir
    tool_paths = ','.join(tool_paths)

    # The prelude option
    prelude = '\timport waflib.extras.wurf.wurf_entry_point'

    # Build the command to execute
    command = "python waf-light configure build --make-waf --prelude='{}' --tools={}".format(
        prelude, tool_paths)

    return tsk.exec_command(command, cwd=wd)

def build(bld):

    # Waf checks that source files are available when we create the
    # different tasks. We can ask waf to lazily do this because the waf
    # binary is not created until after we run the waf-light build
    # step. This is manipulated using the post_mode.
    #bld.post_mode = Build.POST_LAZY

    # We need to invoke the waf-light from within the third_party/waf
    # folder as waf-light will look for wscript in the folder where the
    # executable was started - so we need to start it from the right
    # folder. Using cwd we can make sure the python process is lauched in
    # the right directory.
    #tools = bld.path.ant_glob('tools/*.py')
    #tools += [bld.root.find_node(
    #    os.path.join(bld.dependency_path('python-semver'), 'semver.py'))]

    #bld(rule=build_waf_binary,
    #    source=tools,
    #    cwd=bld.dependency_path('waf'),
    #    always=True)

    # tools = ['tools/wurf_entry_point.py',
    #          'tools/wurf_options_context.py',
    #          'tools/wurf_resolve_context.py',
    #          'tools/wurf_registry.py',
    #          'tools/wurf_git.py',
    #          'tools/wurf_git_url_resolver.py',
    #          'tools/wurf_git_resolver.py',
    #          'tools/wurf_git_checkout_resolver.py',
    #          'tools/wurf_source_resolver.py',
    #          'tools/wurf_user_checkout_resolver.py',
    #          'tools/wurf_user_path_resolver.py']

    tools_dir = ['temp_clones/shutilwhich/shutilwhich',
                 'temp_clones/python-semver/semver.py',
                 'src/wurf']

    bld(rule=build_waf_binary,
        #source=tools,
        cwd='/home/mvp/dev/steinwurf/waf/temp_clones/waf',
        tools_dir=tools_dir,
        always=True)

    bld.add_group()

    # Copy the waf binary to build directory
    bld(features='subst',
        source=bld.root.find_node(
            os.path.join('/home/mvp/dev/steinwurf/waf/temp_clones/waf', 'waf')),
        target=bld.bldnode.make_node('waf'),
        is_copy=True)

    # bld(features='subst',
    #     source=bld.root.find_node(
    #         os.path.join('/home/mvp/dev/steinwurf/waf/temp_clones/waf', 'waf')),
    #     target=bld.bldnode.make_node('waf'),
    #     is_copy=True)


    #bld(features='subst',
    #    source=bld.root.find_node(
    #        os.path.join(bld.dependency_path('waf'), 'waf')),
    #    target=bld.bldnode.make_node('waf'),
    #    is_copy=True)

    # Make a build group will ensure that
    bld.add_group()



    # Invoke tox to run all the pure Python unit tests. Tox creates
    # virtualenvs for different setups and runs unit tests in them. See the
    # tox.ini to see the configuration used and see
    # https://tox.readthedocs.org/ for more information about tox.
    #
    # We run tox at the end since we will use the freshly built waf binary
    # in some of the tests.

    my_env = bld.env.derive()
    my_env.env = os.environ

    #tools_path = os.path.join(os.getcwd(), 'tools')
    semver_path = os.path.join(os.getcwd(), 'third_party', 'python-semver')
    shutil_path = os.path.join(os.getcwd(), 'temp_clones', 'shutilwhich')
    wurf_path = os.path.join(os.getcwd(), 'src')

    my_env.env.update({'PYTHONPATH': ':'.join([wurf_path, semver_path, shutil_path])})

    #print(my_env)
    #print(bld.env)
    bld(rule="env | grep PYTHONPATH", env=my_env, always=True)
    bld(rule='tox', env=my_env, always=True)
    #bld(rule='tox -- -s', env=my_env, always=True)
