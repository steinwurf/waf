import os
import sys
import subprocess
import glob
import time
import mock

from wurf_dependency_bundle import Dependency

def test_dependency():

    resolver = mock.Mock()
    resolver.hash = mock.Mock(return_value='ababab')

    d = Dependency('test', resolver, True, True)
