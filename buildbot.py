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


def configure(properties):
    command = [sys.executable, 'waf', 'configure', '-v', '--zones=resolve']
    run_command(command)


def build(properties):
    command = [sys.executable, 'waf', 'build', '-v', '--zones=resolve']
    run_command(command)


def run_tests(properties):
    command = [sys.executable, 'waf', '-v', '--run_tests', '--zones=resolve']
    run_command(command)


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
