import pytest
import mock
import argparse

from wurf.registry import Registry

class Point(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y

def test_registry():

    registry = Registry()

    def build_point(registry, x=0):
        return Point(x,0)

    registry.provide_function('point', build_point)

    # Use the default build
    with registry.provide_value('x', 0):
        p = registry.require('point')

    assert p.x == 0
    assert p.y == 0

    # Check that we cannot add the same provider twice
    with pytest.raises(Exception):
        registry.provide_function('point', build_point)

    # Bind an argument in the require
    registry.provide_function('point', build_point, override=True)

    with registry.provide_value('x', 1):
        p = registry.require('point')

    assert p.x == 1
    assert p.y == 0

    # Cache the feature
    registry.cache_provider('point')

    with registry.provide_value('x', 1):
        p = registry.require('point')

    assert p.x == 1
    assert p.y == 0

    # Change the value
    p.y = 1

    with registry.provide_value('x', 1):
        p = registry.require('point')

    assert p.x == 1
    assert p.y == 1

    # Ask for a point with a different value, this will bypass the cache
    with registry.provide_value('x', 4):
        p = registry.require('point', x=4)

    assert p.x == 4
    assert p.y == 0

    # Create a new registry
    registry = Registry()

    def build_point(registry, x=0):
        return Point(x,0)

    registry.provide_function('point', build_point)

    # Use the default build
    with registry.provide_value('x', 0):
        p = registry.require('point')

    assert p.x == 0
    assert p.y == 0

    source = 'www.steinwurf.com'

    with registry.provide_value('current_source', source):
        assert 'current_source' in registry
        assert registry.require('current_source') == 'www.steinwurf.com'

    assert 'current_source' not in registry
