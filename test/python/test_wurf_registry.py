import pytest
import mock
import argparse

from wurf import wurf_registry

class Point(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y

def test_wurf_registry():

    registry = wurf_registry.Registry()

    def build_point(registry, x=0):
        return Point(x,0)

    registry.provide('point', build_point)

    # Use the default build
    p = registry.require('point')

    assert p.x == 0
    assert p.y == 0

    # Check that we cannot add the same provider twice
    with pytest.raises(Exception):
        registry.provide('point', build_point)

    # Bind an argument in the require
    registry.provide('point', build_point, override=True)

    p = registry.require('point', x=1)

    assert p.x == 1
    assert p.y == 0


def test_parse_user_path():

    # No path specified
    parser = argparse.ArgumentParser()
    args = ['--foo', '--bundle-path', '-b']

    registry = wurf_registry.Registry()
    registry.provide_value('parser', parser)
    registry.provide_value('args', args)

    dependency = mock.Mock()
    dependency.name = 'foo'

    path = registry.require('user_path', dependency=dependency)
    assert path == None

    # Path specified
    parser = argparse.ArgumentParser()
    args = ['--foo', '--bundle-path', '--foo-path', '/home/stw/code', '-b']

    registry = wurf_registry.Registry()
    registry.provide_value('parser', parser)
    registry.provide_value('args', args)

    path = registry.require('user_path', dependency=dependency)
    assert path == '/home/stw/code'

    print(registry.registry)