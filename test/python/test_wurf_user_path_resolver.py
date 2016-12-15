import pytest
import mock
import argparse

from wurf.wurf_user_path_resolver import WurfUserPathResolver

def test_wurf_user_path_resolver_default():

    parser = argparse.ArgumentParser()
    args = ['--foo', '-b']
    
    resolver = WurfUserPathResolver(parser, args)
    
    ret = resolver.resolve('test')
    
    assert(ret == None)


def test_wurf_user_path_resolver():

    parser = argparse.ArgumentParser()
    args = ['--foo', '--test-path', '/home/stw/code', '-b']

    resolver = WurfUserPathResolver(parser, args)
    
    ret = resolver.resolve('test')
    
    assert(ret == '/home/stw/code')
