import os
import sys
import subprocess
import glob
import time


def test_copy_file(test_directory):
    test_directory.copy_files('test/prog1/*')
    test_directory.copy_file('build/*/waf')

    r = test_directory.run('python','waf','configure')

    assert r.returncode == 0
    assert r.stdout.match('*finished successfully*')

    r = test_directory.run('python', 'waf', 'build')

    assert r.returncode == 0
