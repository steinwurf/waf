import pytest
import mock
import argparse

from wurf.wurf_source_resolver import WurfBundlePath

def test_wurf_bundle_path_default():

    parser = argparse.ArgumentParser()
    default_bundle_path = '/tmp/okidoki'
    args = ['--foo', '-b']
    utils = mock.Mock()

    bundle = WurfBundlePath(utils=utils,
        parser=parser, default_bundle_path=default_bundle_path, args=args)

    bundle.next_resolver = mock.Mock()
    bundle.add_dependency()

    bundle.next_resolver.add_dependency.assert_called_once_with(
        bundle_path=default_bundle_path)

    utils.check_dir.assert_called_once_with(path=default_bundle_path)

def test_wurf_bundle_path_no_default():

    parser = argparse.ArgumentParser()
    default_bundle_path = '/tmp/okidoki'
    args = ['--foo', '--bundle-path', '/home/stw/code', '-b']
    utils = mock.Mock()

    bundle = WurfBundlePath(utils=utils, parser=parser,
        default_bundle_path=default_bundle_path, args=args)

    bundle.next_resolver = mock.Mock()

    bundle.add_dependency()

    bundle.next_resolver.add_dependency.assert_called_once_with(
        bundle_path='/home/stw/code')

    utils.check_dir.assert_called_once_with(path='/home/stw/code')
