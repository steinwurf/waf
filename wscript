#! /usr/bin/env python
# encoding: utf-8

import os
import sys

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

    ctx.add_dependency(
        name='python-archive',
        recurse=False,
        optional=False,
        resolver='git',
        method='checkout',
        checkout='toolify',
        sources=['github.com/steinwurf/python-archive.git'])

    # Testing dependencies

    ctx.add_dependency(
        name='virtualenv',
        recurse=False,
        optional=False,
        resolver='git',
        method='checkout',
        checkout='15.1.0',
        sources=['github.com/pypa/virtualenv.git'])


def options(opt):

    opt.add_option(
        '--run_tests', default=False, action='store_true',
        help='Run all unit tests')

    opt.add_option(
        '--test_filter', default=None, action='store',
        help='Runs all tests that include the substring specified.'
             'Wildcards not allowed. (Used with --run_tests)')

    opt.add_option(
        '--pytest_basetemp', default='pytest',
        help='Set the basetemp folder where pytest executes the tests')

    opt.add_option(
        '--skip_network_tests', default=False, action='store_true',
        help='Skip the unit tests that use network resources')


def _create_virtualenv(ctx, cwd):
    # Make sure the virtualenv Python module is in path
    venv_path = ctx.dependency_path('virtualenv')

    env = dict(os.environ)
    env.update({'PYTHONPATH': os.path.pathsep.join([venv_path])})

    from waflib.extras.wurf.virtualenv import VirtualEnv
    return VirtualEnv.create(cwd=cwd, env=env, name=None, ctx=ctx,
                             pip_packages_path=os.path.join(ctx.path.abspath(),
                                                            'pip_packages'))


def configure(conf):

    # Ensure that the waf-light program is available in the in the
    # waf folder. This is used to build the waf binary.
    conf.find_program('waf-light', exts='',
                      path_list=[conf.dependency_path('waf')])


def _build_waf_binary(bld):
    """ Build the waf binary."""

    tools_dir = [
        os.path.join(bld.dependency_path('python-semver'), 'semver.py'),
        os.path.join(bld.dependency_path('python-archive'), 'archive'),
        'src/wurf'
    ]

    tools_dir = [os.path.abspath(os.path.expanduser(d)) for d in tools_dir]

    # waf-light will look for the wscript in the folder where the process
    # is started, so we must run this command in the folder where we
    # resolved the waf dependency.
    cwd = bld.dependency_path('waf')

    # Run with ./waf --zones wurf to see the print
    waflib.Logs.debug("wurf: tools_dir={}".format(tools_dir))

    # Get the absolute path to all the tools (passed as input to the task)
    tool_paths = ','.join(tools_dir)

    # The prelude option
    prelude = '\timport waflib.extras.wurf.waf_entry_point'

    # Build the command to execute
    python = sys.executable
    command = python + ' waf-light configure build --make-waf '\
                       '--prelude="{}" --tools={}'.format(prelude, tool_paths)

    bld.cmd_and_log(command, cwd=cwd)

    # Copy the waf binary to the build folder
    waf_src = bld.root.find_resource(os.path.join(cwd, 'waf'))
    waf_dest = bld.bldnode.make_node('waf')
    waf_dest.write(waf_src.read('rb'), 'wb')

    bld.msg("Build waf binary", waf_dest.abspath())


def build(bld):

    # Create a log file for the output
    path = os.path.join(bld.bldnode.abspath(), 'build.log')
    bld.logger = waflib.Logs.make_logger(path, 'cfg')

    _build_waf_binary(bld=bld)

    if bld.options.run_tests:
        _pytest(bld=bld)


def _pytest(bld):

    venv = _create_virtualenv(ctx=bld, cwd=bld.path.abspath())

    with venv:

        venv.pip_install('pytest', 'mock', 'vcrpy', 'pytest-testdirectory',
                         'pep8', 'pyflakes')

        # Add our sources to the Python path
        python_path = [
            bld.dependency_path('python-semver'),
            os.path.join(os.getcwd(), 'src')
        ]

        venv.env.update({'PYTHONPATH': os.path.pathsep.join(python_path)})
        venv.env['PATH'] = os.path.pathsep.join(
            [venv.env['PATH'], os.environ['PATH']])

        # We override the pytest temp folder with the basetemp option,
        # so the test folders will be available at the specified location
        # on all platforms. The default location is the "pytest" local folder.
        basetemp = os.path.abspath(os.path.expanduser(
            bld.options.pytest_basetemp))

        # We need to manually remove the previously created basetemp folder,
        # because pytest uses os.listdir in the removal process, and that fails
        # if there are any broken symlinks in that folder.
        if os.path.exists(basetemp):
            waflib.extras.wurf.directory.remove_directory(path=basetemp)

        # Make python not write any .pyc files. These may linger around
        # in the file system and make some tests pass although their .py
        # counter-part has been e.g. deleted
        command = 'python -B -m pytest test --basetemp ' + basetemp

        # Conditionally disable the tests that have the "networktest" marker
        if bld.options.skip_network_tests:
            command += ' -m "not networktest"'

        # Adds the test filter if specified
        if bld.options.test_filter:
            command += ' -k ' + bld.options.test_filter

        venv.run(command)

        # Run PEP8 check
        bld.msg("Running", "pep8")
        venv.run('python -m pep8 --filename=*.py,wscript '
                 'src test wscript buildbot.py')

        # Run pyflakes
        bld.msg("Running", "pyflakes")
        venv.run('python -m pyflakes src test')
