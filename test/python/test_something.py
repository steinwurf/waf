import os
import sys
import subprocess

import pytest
import py

def run_command(args):
    print("Running: {}".format(args))
    sys.stdout.flush()
    subprocess.check_call(args)



class TestDir:
    def __init__(self, request, tmpdir):
        self.tmpdir = tmpdir
        print(tmpdir)

    def copy_file(self, filename):
        # Copy the file to the tmpdir
        filepath = py.path.local(filename)
        filepath.copy(self.tmpdir)
        print(filepath)
        print("SHHHHOT")



@pytest.fixture
def testdir(request, tmpdir):
    return TestDir(request, tmpdir)

def test_copy_file(testdir):
    testdir.copy_file('test/prog1/wscript')
    #command = [sys.executable, 'waf', 'build', '-v']
    #run_command(command)
