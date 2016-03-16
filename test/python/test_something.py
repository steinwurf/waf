import os
import sys
import subprocess

def run_command(args):
    print("Running: {}".format(args))
    sys.stdout.flush()
    subprocess.check_call(args)


class TestCLI:
    def __init__(self, request, tmpdir_factory):
        pass

def test_copy_files(tmpdir_factory):
    pass
    #command = [sys.executable, 'waf', 'build', '-v']
    #run_command(command)
