import pytest
import py
import glob
import subprocess
import time
import os

from . import runresult

class TestDirectory:
    """Testing code by invoking executable which potentially creates and deletes
    files and directories can be hard and error prone.

    The purpose of this module is to simplify this task.

    To make it easy to use in with pytest the TestDirectory object can be
    injected into a test function by using the testdirectory fixture (defined
    below this class).

    Example:

        def test_this_function(testdirectory):
            images = testdirectory.mkdir('images')
            images.copy_files('test/images/*')

            r = testdirectory.run('imagecompress --path=images')

            # r is an RunResult object containing information about the command
            # we just executed
            assert r.returncode == 0

    The testdirectory is an instance of TestDirectory and represents an actual
    temporary directory somewhere on the machine running the test code. Using
    the API we can create additional temporary directories, populate them with
    an initial set of files and finally run some executable and observe its
    behavior.

    inspiration: http://search.cpan.org/~sanbeg/Test-Directory-0.041/lib/Test/Directory.pm
    """
    def __init__(self, tmpdir):
        self.tmpdir = tmpdir

    def mkdir(self, name):
        """Create a sub-directory in the temporary / test dir.
        """
        return TestDirectory(self.tmpdir.mkdir(name))

    def path(self):
        """ :return: The path to the temporary directory as a string"""
        return str(self.tmpdir)

    def copy_file(self, filename):

        # Expand filename by expanding wildcards e.g. 'dir/*/file.txt', the
        # glob should return only one file
        files = glob.glob(filename)

        assert len(files) == 1

        filename = files[0]

        # Copy the file to the tmpdir
        filepath = py.path.local(filename)
        filepath.copy(self.tmpdir)
        print("Copy: {} -> {}".format(filepath, self.tmpdir))

    def copy_files(self, filename):

        # Expand filename by expanding wildcards e.g. 'dir/*', the
        # glob returns a list of files
        files = glob.glob(filename)

        for f in files:
            self.copy_file(f)

    def copy_dir(self, directory):
        """Copy a directory into the test directory."""

        # From: http://stackoverflow.com/a/3925147
        name = os.path.basename(os.path.normpath(directory))

        # We need to create the directory
        target_dir = self.tmpdir.mkdir(name)

        source_dir = py.path.local(directory)
        source_dir.copy(target_dir)

        print("Copy Dir: {} -> {}".format(source_dir, target_dir))


    def write_file(self, filename, content):
        """Writes a file in the temporary directory.

        """

        f = self.tmpdir.join(filename)
        f.write(content)


    def run(self, *args, **kwargs):
        """Runs the command in the test directory.

        If 'env' is not passed as keyword argument use a copy of the
        current environment.

        :param args: List of arguments
        :param kwargs: Keyword arguments passed to Popen(...)

        :return: A RunResult object representing the result of the command
        """

        if 'env' in kwargs:
            env = kwargs
            del kwargs['env']
        else:
            env = os.environ.copy()

        print(env)

        start_time = time.time()

        popen = subprocess.Popen(args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    # Need to decode the stdout and stderr with the correct
                    # character encoding (http://stackoverflow.com/a/28996987)
                    universal_newlines=True,

                    env=env,

                    # Sets the current working directory to the path of
                    # the tmpdir
                    cwd=str(self.tmpdir))

        stdout, stderr = popen.communicate()

        end_time = time.time()

        return runresult.RunResult(' '.join(args), self.path(),
            stdout, stderr, popen.returncode, end_time - start_time)
