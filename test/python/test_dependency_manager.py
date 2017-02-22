import sys
import os
from collections import OrderedDict

import mock

from wurf.dependency_manager import DependencyManager

def test_dependency_manager():

    registry = mock.Mock()
    dependency_cache = OrderedDict()
    ctx = mock.Mock()
    options = mock.Mock()

    d = DependencyManager(registry=registry, dependency_cache=dependency_cache,
                          ctx=ctx, options=options)

    # @todo add tests
