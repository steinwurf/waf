import pytest
import py
import glob
import subprocess
import time

import runresult

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

    Then, whenever something in the
    directory is changes, use the test methods to verify that the change
    happened as expected. At any time, it is simple to verify that the
    contents of the directory are exactly as expected.

    Test::Directory implements an object-oriented interface for managing
    test directories. It tracks which files it knows about (by creating
    or testing them via its API), and can report if any files were
    missing or unexpectedly added.

    There are two flavors of methods for interacting with the
    directory. Utility methods simply return a value (i.e. the number of
    files/errors) with no output, while the Test functions use
    Test::Builder to produce the approriate test results and diagnostics
    for the test harness.

    The directory will be automatically cleaned up when the object goes
    out of scope; see the clean method below for details.
    """
    def __init__(self, tmpdir):
        self.tmpdir = tmpdir

    def dir(self):
        return self.tmpdir

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

    def write_file(self, filename, content):

        f = self.tempdir.join(filename)
        f.write(content)


    def run(self, *args):
        """Runs the command in the test directory

        :param args: List of arguments

        :return: A RunResult object representing the result of the command
        """

        start_time = time.time()

        popen = subprocess.Popen(args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    # Need to decode the stdout and stderr with the correct
                    # character encoding (http://stackoverflow.com/a/28996987)
                    universal_newlines=True,

                    # Sets the current working directory to the path of
                    # the tmpdir
                    cwd=str(self.tmpdir))

        stdout, stderr = popen.communicate()

        end_time = time.time()

        return runresult.RunResult(' '.join(args),
            stdout, stderr, popen.returncode, end_time - start_time)

@pytest.fixture
def testdirectory(tmpdir):
    return TestDirectory(tmpdir)
