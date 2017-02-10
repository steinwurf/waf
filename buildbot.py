#!/usr/bin/env python
# encoding: utf-8

import os
import sys
import json
import shutil
import subprocess

project_name = 'waf'


def run_command(args, cwd=None, env=None):
    print("Running: {}".format(args))
    sys.stdout.flush()
    subprocess.check_call(args, cwd=cwd, env=env)


#def get_tool_options(properties):
#    options = []
#    if 'tool_options' in properties:
#        # Make sure that the values are correctly comma separated
#        for key, value in properties['tool_options'].items():
#            if value is None:
#                options += ['--{0}'.format(key)]
#            else:
#                options += ['--{0}={1}'.format(key, value)]
#
#    return options


def configure(properties):
    pass


def build(properties):
    #run_command(['git', 'submodule', 'init'])
    #run_command(['git', 'submodule', 'update'])

    # The waf-light script used to build the waf binary is
    # located in the third_party/waf folder
    cwd = os.getcwd()
    waf_path = os.path.join(cwd, 'third_party', 'waf')

    third_party = os.path.join(cwd, 'third_party')

    # Add the absolute paths to all the necessary tools
    tools = [os.path.join(third_party, 'shutilwhich', 'shutilwhich'),
             os.path.join(third_party, 'python-semver', 'semver.py'),
             os.path.join(cwd, 'src', 'wurf')]

    tool_paths = ','.join(tools)

    # The prelude option
    prelude = '\timport waflib.extras.wurf.wurf_entry_point'

    command = ['python', 'waf-light', 'configure', 'build', '--make-waf']
    command += ['--prelude={}'.format(prelude)]
    command += ['--tools={}'.format(tool_paths)]

    # Run waf-light to build the waf binary
    run_command(command, cwd=waf_path)

    # Copy the waf binary to the build folder
    waf_binary = os.path.join(waf_path, 'waf')
    target_dir = 'build'
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    shutil.copy(waf_binary, target_dir)


def run_tests(properties):
    env = dict(os.environ)
    cwd = os.getcwd()
    third_party = os.path.join(cwd, 'third_party')

    # Add the absolute paths to all the necessary packages
    tools = [os.path.join(third_party, 'pytest'),
             os.path.join(third_party, 'py'),
             os.path.join(third_party, 'mock'),
             os.path.join(third_party, 'shutilwhich'),
             os.path.join(third_party, 'python-semver'),
             os.path.join(cwd, 'src')]

    separator = ';' if sys.platform == 'win32' else ':'
    env['PYTHONPATH'] = separator.join(tools)

    # Remove the previously created temp folder
    if os.path.exists('temp'):

        def onerror(func, path, exc_info):
            import stat
            if not os.access(path, os.W_OK):
                # Is the error an access error ?
                os.chmod(path, stat.S_IWUSR)
                func(path)
            else:
                raise

        shutil.rmtree('temp', onerror=onerror)

    # Run the unit tests with pytest
    command = [sys.executable, '-m', 'pytest', '-x', '--basetemp=temp', 'test']
    run_command(command, env=env)


def install(properties):
    pass


def main():
    argv = sys.argv

    if len(argv) < 2:
        print("Usage: {} <command> <properties>".format(argv[0]))
        sys.exit(0)

    cmd = argv[1]
    properties = {}
    if len(argv) == 3:
        properties = json.loads(argv[2])

    if cmd == 'configure':
        configure(properties)
    elif cmd == 'build':
        build(properties)
    elif cmd == 'run_tests':
        run_tests(properties)
    elif cmd == 'install':
        install(properties)
    else:
        print("Unknown command: {}".format(cmd))


if __name__ == '__main__':
    main()
