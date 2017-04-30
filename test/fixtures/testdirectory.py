import pytest
import py
import glob
import subprocess
import time
import os

from . import runresult
from . import runresulterror

class TestDirectory(object):
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

        if isinstance(tmpdir, py.path.local):
            self.tmpdir = tmpdir
        else:
            self.tmpdir = py.path.local(path=tmpdir)

    @staticmethod
    def from_path(path):
        """Create a new TestDirectory instance from a path.

        :param path: The path as a string.
        """
        assert os.path.isdir(path)
        return TestDirectory(py.path.local(path))

    def mkdir(self, directory):
        """Create a sub-directory in the temporary / test dir.

        :param directory: The
        """
        return TestDirectory(self.tmpdir.mkdir(directory))

    def rmdir(self):
        """ Remove the directory."""
        self.tmpdir.remove()

        # @todo not sure if this is a good idea, but I guess the tmpdir is
        # invalid after the remove?
        self.tmpdir = None

    def join(self, *args):
        """ Get a TestDirectory instance representing a path.

        """
        path = self.tmpdir.join(*args)
        assert path.isdir()

        return TestDirectory(tmpdir=path)

    def rmfile(self, filename):
        """ Remove a file.

        :param filename The name of the file to remove as a string
        """
        os.remove(os.path.join(self.path(), filename))

    def path(self):
        """ :return: The path to the temporary directory as a string"""
        return str(self.tmpdir)

    def copy_file(self, filename, rename_as=""):
        """ Copy the file to the test directory.

        :param filename: The filename as a string.
        :param rename_as: If specified rename the file represented by filename
            to the name given in rename_as as a string.
        :return: The path to the file in its new location as a string.
        """

        # Expand filename by expanding wildcards e.g. 'dir/*/file.txt', the
        # glob should return only one file
        files = glob.glob(filename)

        print(filename)
        print(files)

        assert len(files) == 1

        filename = files[0]

        # Copy the file to the tmpdir
        filepath = py.path.local(filename)
        filepath.copy(self.tmpdir)

        print("Copy: {} -> {}".format(filepath, self.tmpdir))

        filepath = self.tmpdir.join(filepath.basename)
        if rename_as:
            target = self.tmpdir.join(rename_as)
            filepath.rename(target)
            print("Rename: {} -> {}".format(filepath, target))
            filepath = target

        return str(filepath)

    def copy_files(self, filename):

        # Expand filename by expanding wildcards e.g. 'dir/*', the
        # glob returns a list of files
        files = glob.glob(filename)

        for f in files:
            self.copy_file(f)

    def copy_dir(self, directory):
        """Copy a directory into the test directory.

        Example (using the test fixture test_directory):

            def test_something(test_directory):

                # Prints /tmp/pytest-9/some_test
                print(test_directory.path())

                app_dir = test_directory.copy_dir('/home/ok/app')

                # Prints /tmp/pytest-9/some_test/app
                print(app_dir.path())

        :param directory: Path to the directory as a string
        :return: TestDirectory object representing the copied directory
        """

        # From: http://stackoverflow.com/a/3925147
        name = os.path.basename(os.path.normpath(directory))

        # We need to create the directory
        target_dir = self.tmpdir.mkdir(name)

        source_dir = py.path.local(directory)
        source_dir.copy(target_dir)

        print("Copy Dir: {} -> {}".format(source_dir, target_dir))

        return TestDirectory(target_dir)

    def write_text(self, filename, data, encoding):
        """Writes a file in the temporary directory.

        """

        f = self.tmpdir.join(filename)
        f.write_text(data=data, encoding=encoding)

    def write_binary(self, filename, data):
        """Writes a file in the temporary directory.

        """

        f = self.tmpdir.join(filename)

        print(type(f.strpath))

        f.write_binary(data=data)

    def contains_file(self, filename):
        """ Checks for the existance of a file.

        :param filename: The filename to check for.
        :return: True if the file is contained within the test directory.
        """
        files = glob.glob(os.path.join(self.path(), filename))

        if len(files) == 0:
            return False

        assert(len(files) == 1)

        filename = files[0]

        return os.path.isfile(filename)

    def contains_dir(self, *directories):
        """ Checks for the existance of a directory.

        :param dirname: The directory name to check for.
        :return: True if the directory is contained within the test directory.
        """

        # Expand filename by expanding wildcards e.g. 'dir/*/file.txt', the
        # glob should return only one file
        directories = glob.glob(os.path.join(self.path(), *directories))

        if len(directories) != 1:
            return False

        # Follow symlinks
        if not os.path.exists(directories[0]):
            return False

        return True

    def run(self, *args, **kwargs):
        """Runs the command in the test directory.

        If 'env' is not passed as keyword argument use a copy of the
        current environment.

        :param args: List of arguments
        :param kwargs: Keyword arguments passed to Popen(...)

        :return: A RunResult object representing the result of the command
        """

        if 'env' in kwargs:
            env = kwargs['env']
            del kwargs['env']
        else:
            env = os.environ.copy()

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

        result = runresult.RunResult(' '.join(args), self.path(),
            stdout, stderr, popen.returncode, end_time - start_time)

        if popen.returncode != 0:
            raise runresulterror.RunResultError(result)

        return result
