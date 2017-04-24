#! /usr/bin/env python
# encoding: utf-8

import os
import sys
import shutil

import waflib

top = '.'

def resolve(ctx):

    ctx.add_dependency(
        name='waf',
        recurse=False,
        optional=False,
        resolver='git',
        method='checkout',
        # The next release after waf 1.9.8 should contain the fix for the
        # Windows build issue: https://github.com/waf-project/waf/pull/1915
        checkout='e596b529d8',
        sources=['github.com/waf-project/waf.git'])

    ctx.add_dependency(
        name='python-semver',
        recurse=False,
        optional=False,
        resolver='git',
        method='checkout',
        checkout='2.4.1',
        sources=['github.com/k-bx/python-semver.git'])

    # Testing dependencies

    ctx.add_dependency(
        name='pytest',
        recurse=False,
        optional=False,
        resolver='git',
        method='checkout',
        checkout='3.0.6',
        sources=['github.com/pytest-dev/pytest.git'])

    ctx.add_dependency(
        name='py',
        recurse=False,
        optional=False,
        resolver='git',
        method='checkout',
        checkout='1.4.32',
        sources=['github.com/pytest-dev/py.git'])

    ctx.add_dependency(
        name='mock',
        recurse=False,
        optional=False,
        resolver='git',
        method='checkout',
        checkout='1.0.1',
        sources=['github.com/testing-cabal/mock.git'])


def options(opt):

    opt.add_option(
        '--run_tests', default=False, action='store_true',
        help='Run all unit tests')

    opt.add_option(
        '--pytest_basetemp', default='pytest',
        help='Set the basetemp folder where pytest executes the tests')

    opt.add_option(
        '--skip_network_tests', default=False, action='store_true',
        help='Skip the unit tests that use network resources')


def configure(conf):

    # Ensure that the waf-light program is available in the in the
    # waf folder. This is used to build the waf binary.
    conf.find_program('waf-light', exts='',
        path_list=[conf.dependency_path('waf')])


def build_waf_binary(tsk):
    """
    Task for building the waf binary.
    """

    # Get the working directory
    # Waf checks whether a path is a waflib.Node or string by checking
    # isinstance(str) but in python3 most string are unicode, which makes the
    # test fail.
    wd = str(getattr(tsk, 'cwd', None))

    # Tools dir
    tools_dir = getattr(tsk.generator, 'tools_dir', None)
    tools_dir = [os.path.abspath(os.path.expanduser(d)) for d in tools_dir]

    # Run with ./waf --zones wurf to see the print
    waflib.Logs.debug("wurf: tools_dir={}".format(tools_dir))

    # Get the absolute path to all the tools (passed as input to the task)
    tool_paths = [t.abspath() for t in tsk.inputs] + tools_dir
    tool_paths = ','.join(tool_paths)

    # The prelude option
    prelude = '\timport waflib.extras.wurf.waf_entry_point'

    # Build the command to execute
    command = 'python waf-light configure build --make-waf --prelude="{}" '\
              '--tools={}'.format(prelude, tool_paths)

    # Get the waf BuildContext
    bld = tsk.generator.bld
    bld.cmd_and_log(command, cwd=wd, quiet=waflib.Context.BOTH)

    # Copy the waf binary to the build folder
    waf_src = bld.root.find_resource(os.path.join(wd, 'waf'))
    waf_dest = bld.bldnode.make_node('waf')
    waf_dest.write(waf_src.read('rb'), 'wb')


def build(bld):

    tools_dir = \
    [
        os.path.join(bld.dependency_path('python-semver'), 'semver.py'),
        'src/wurf'
    ]

    # waf-light will look for the wscript in the folder where the process
    # is started, so we must run this command in the folder where we
    # resolved the waf dependency.
    bld(rule=build_waf_binary,
        cwd=bld.dependency_path('waf'),
        tools_dir=tools_dir,
        always=True)

    bld.add_group()

    if bld.options.run_tests:
        _pytest(bld=bld)


def _pytest(bld):

    python_path = \
    [
        bld.dependency_path('pytest'),
        bld.dependency_path('py'),
        bld.dependency_path('mock'),
        bld.dependency_path('python-semver'),
        os.path.join(os.getcwd(), 'src')
    ]

    bld_env = bld.env.derive()
    bld_env.env = dict(os.environ)

    separator = ';' if sys.platform == 'win32' else ':'
    bld_env.env.update({'PYTHONPATH': separator.join(python_path)})

    # Make python not write any .pyc files. These may linger around
    # in the file system and make some tests pass although their .py
    # counter-part has been e.g. deleted
    test_command = 'python -B -m pytest test'

    # We override the pytest temp folder with the basetemp option,
    # so the test folders will be available at the specified location
    # on all platforms. The default location is the "pytest" local folder.

    basetemp = os.path.abspath(os.path.expanduser(bld.options.pytest_basetemp))
    test_command += ' --basetemp {}'.format(basetemp)

    # We need to manually remove the previously created basetemp folder,
    # because pytest uses os.listdir in the removal process, and that fails
    # if there are any broken symlinks in that folder.
    # Note that shutil.rmtree fails with the same error, so we use os.walk
    # to traverse the directory tree from the bottom up as recommended here:
    # http://stackoverflow.com/a/2656408
    if os.path.exists(basetemp):

        def rmtree(top):
            import stat

            # In Python2 convert to unicode
            try:
                top = unicode(top)
            except NameError:
                pass

            for root, dirs, files in os.walk(top, topdown=False):
                for name in files:
                    filename = os.path.join(root, name)
                    if not os.path.islink(filename):
                        os.chmod(filename, stat.S_IWUSR)
                    os.remove(filename)
                for name in dirs:
                    dir = os.path.join(root, name)
                    if os.path.islink(dir):
                        os.unlink(dir)
                    else:
                        os.rmdir(dir)
            os.rmdir(top)

        rmtree(basetemp)

    # Conditionally disable the tests that have the "networktest" marker
    if bld.options.skip_network_tests:
        test_command += ' -m "not networktest"'

    bld(rule=test_command,
        cwd=bld.path,
        env=bld_env,
        always=True)
