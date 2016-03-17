import os
import sys
import subprocess

import pytest
import py

def run_command(args):
    print("Running: {}".format(args))
    sys.stdout.flush()
    subprocess.check_call(args)



class TestCLI:
    def __init__(self, request, tmpdir):
        self.tmpdir = tmpdir#tmpdir.mkdir('data')
        print(tmpdir)

    def copy_file(self, filename):
        path = py.path.local(filename)
        path.copy(self.tmpdir)
        print(path)
        print("SHHHHOT")



@pytest.fixture
def test_cli(request, tmpdir):
    return TestCLI(request, tmpdir)

def test_copy_files(test_cli):
    test_cli.copy_file('test/prog1/wscript')
    #command = [sys.executable, 'waf', 'build', '-v']
    #run_command(command)
