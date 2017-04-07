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

    def build_point(registry, x):
        return Point(x,0)

    registry.provide_function('point', build_point)

    # Use the default build
    with registry.provide_temporary() as tmp:
        tmp.provide_value('x', 0)
        p = registry.require('point')

    assert p.x == 0
    assert p.y == 0

    # Check that we cannot add the same provider twice
    with pytest.raises(Exception):
        registry.provide_function('point', build_point)

    # Bind an argument in the require
    registry.provide_function('point', build_point, override=True)

    with registry.provide_temporary() as tmp:
        tmp.provide_value('x', 1)
        p = registry.require('point')

    assert p.x == 1
    assert p.y == 0

    # Cache the feature
    registry.cache_provider('point')

    with registry.provide_temporary() as tmp:
        tmp.provide_value('x', 1)
        p = registry.require('point')

    assert p.x == 1
    assert p.y == 0

    # Change the value
    p.y = 1

    with registry.provide_temporary() as tmp:
        tmp.provide_value('x', 1)
        p = registry.require('point')

    assert p.x == 1
    assert p.y == 1

    # Ask for a point with a different value, this will bypass the cache
    with registry.provide_temporary() as tmp:
        tmp.provide_value('x', 4)
        p = registry.require('point')

    assert p.x == 4
    assert p.y == 0

    # Create a new registry
    registry = Registry()

    def build_point(registry, x):
        return Point(x,0)

    registry.provide_function('point', build_point)

    # Use the default build
    with registry.provide_temporary() as tmp:
        tmp.provide_value('x', 0)
        p = registry.require('point')

    assert p.x == 0
    assert p.y == 0

    source = 'www.steinwurf.com'

    with registry.provide_temporary() as tmp:
        tmp.provide_value('current_source', source)
        assert 'current_source' in registry
        assert registry.require('current_source') == 'www.steinwurf.com'

    assert 'current_source' not in registry


def test_registry_inject():

    registry = Registry()

    # No arguments
    def build_point():
        return Point(x=0, y=2)

    registry.provide_function('point', build_point)

    p = registry.require('point')
    assert p.x == 0
    assert p.y == 2

    registry = Registry()

    # One argument
    def build_point(y):
        return Point(x=0, y=y)

    registry.provide_function('point', build_point)

    with pytest.raises(Exception):
        p = registry.require('point')

    with registry.provide_temporary() as tmp:
        tmp.provide_value('y', 5)

        p = registry.require('point')

    assert p.x == 0
    assert p.y == 5

    registry = Registry()

    def build_point(y, registry):
        return Point(x=0, y=y)

    registry.provide_function('point', build_point)

    with pytest.raises(Exception):
        p = registry.require('point')

    with registry.provide_temporary() as tmp:
        tmp.provide_value('y', 5)

        p = registry.require('point')

    assert p.x == 0
    assert p.y == 5

    registry = Registry()

    # No arguments
    def build_point(somevalue, othervalue):
        return Point(x=0, y=2)

    registry.provide_function('point', build_point)

    with pytest.raises(Exception):
        p = registry.require('point')


def test_registry_cache():

    registry = Registry()

    class Foo(object):
        def __init__(self): pass

    class Bar(object):
        def __init__(self): pass

    def build_foo():
        return Foo()

    def build_bar(foo):
        return Bar()

    registry.provide_function('foo', build_foo)
    registry.provide_function('bar', build_bar)
    registry.cache_provider('foo')
    registry.cache_provider('bar')



    f = registry.require('foo')
    b = registry.require('bar')
