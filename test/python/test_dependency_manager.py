from collections import OrderedDict

import mock

from wurf.dependency_manager import DependencyManager


def test_dependency_manager():

    registry = mock.Mock()
    dependency_cache = OrderedDict()
    ctx = mock.Mock()
    options = mock.Mock()

    DependencyManager(registry=registry, dependency_cache=dependency_cache,
                      ctx=ctx, options=options, skip_internal=False)

    # @todo add tests
