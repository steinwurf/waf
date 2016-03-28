import os
import pytest
from . import testdirectory

@pytest.fixture
def test_directory(tmpdir):
    """ Creates the PyTest fixture to make it usable withing the unit tests.
    See the TestDirectory class in testdirectory.py for more information.
    """
    return testdirectory.TestDirectory(tmpdir)


def test_fixture(test_directory):
    """ Unit test for the test_directory fixture"""
    assert os.path.exists(test_directory.dir())
