import sys
import os

import unittest
import mock

from wurf.dependency_manager import DependencyManager

def test_dependency_manager():

    registry = mock.Mock()
    cache = {}
    ctx = mock.Mock()

    d = DependencyManager(registry=registry, cache=cache, ctx=ctx)

    # @todo add tests
