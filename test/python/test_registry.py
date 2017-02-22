import pytest
import mock
import argparse

from wurf.registry import Registry

class Point(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y

def test_wurf_registry():

    registry = Registry()

    def build_point(registry, x=0):
        return Point(x,0)

    registry.provide_function('point', build_point)

    # Use the default build
    p = registry.require('point')

    assert p.x == 0
    assert p.y == 0

    # Check that we cannot add the same provider twice
    with pytest.raises(Exception):
        registry.provide_function('point', build_point)

    # Bind an argument in the require
    registry.provide_function('point', build_point, override=True)

    p = registry.require('point', x=1)

    assert p.x == 1
    assert p.y == 0

    # Cache the feature
    registry.cache_provider('point')

    p = registry.require('point', x=1)

    assert p.x == 1
    assert p.y == 0

    # Change the value
    p.y = 1

    p = registry.require('point', x=1)

    assert p.x == 1
    assert p.y == 1

    # Ask for a point with a different value, this will bypass the cache
    p = registry.require('point', x=4)

    assert p.x == 4
    assert p.y == 0

    # Create a new registry
    registry = Registry()

    def build_point(registry, x=0):
        return Point(x,0)

    registry.provide_function('point', build_point)

    # Use the default build
    p = registry.require('point')

    assert p.x == 0
    assert p.y == 0
