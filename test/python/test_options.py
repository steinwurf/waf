import pytest
import mock
import argparse

from wurf.registry import Options

def test_parse_user_path():

    # No path specified
    parser = argparse.ArgumentParser()
    args = ['--foo', '--bundle-path', '/tmp/bundlehere', '-b']

    options = Options(args=args, parser=parser, default_bundle_path="",
        default_symlinks_path="", supported_git_protocols="")

    assert options.bundle_path() == '/tmp/bundlehere'

    dependency = mock.Mock()
    dependency.name = 'foo'

    options.add_dependency(dependency)

    assert options.path(dependency=dependency) == None

    # Path specified
    parser = argparse.ArgumentParser()
    args = ['--foo', '--bundle-path', '/tmp/bundlehere',
            '--foo-path', '/home/stw/code', '-b']

    options = Options(args=args, parser=parser, default_bundle_path="",
        default_symlinks_path="", supported_git_protocols="")

    options.add_dependency(dependency)

    assert options.path(dependency=dependency) == '/home/stw/code'

    # Path specified
    parser = argparse.ArgumentParser()
    args = ['--foo', '--bundle-path', '/tmp/bundlehere',
            '--foo-path', '/home/stw/code1', '-b']

    options = Options(args=args, parser=parser, default_bundle_path="",
        default_symlinks_path="", supported_git_protocols="")

    options.add_dependency(dependency)

    assert options.path(dependency=dependency) == '/home/stw/code1'
