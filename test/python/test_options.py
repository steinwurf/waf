import mock
import argparse
import pytest

from wurf.options import Options
from wurf.error import WurfError


def test_resolve_path():

    default_path = 'resolved_dependencies'

    # Test that if no resove path is specified the default
    # is returned
    parser = argparse.ArgumentParser()
    args = ['--foo', '-b']

    options = Options(args=args, parser=parser,
                      default_resolve_path=default_path,
                      default_symlinks_path="symlinks_path",
                      supported_git_protocols="")

    assert options.resolve_path() == default_path

    # Test that if a resolve path is specified then it is returned
    parser = argparse.ArgumentParser()
    args = ['--foo', '--resolve_path', '/tmp/bundlehere', '-b']

    options = Options(args=args, parser=parser,
                      default_resolve_path=default_path,
                      default_symlinks_path="symlinks_path",
                      supported_git_protocols="")

    assert options.resolve_path() == '/tmp/bundlehere'

    # Test that an exception is raised if an empty resolve path
    # is specified. This simulates the case where a user by accident
    # calls './waf --resolve_path= /tmp/...' should have been:
    # './waf --resolve_path=/tmp/...'. Notice the space after the equal
    # sign.
    parser = argparse.ArgumentParser()
    args = ['--resolve_path=', '/tmp/bundlehere']

    with pytest.raises(SystemExit):
        options = Options(args=args, parser=parser,
                          default_resolve_path=default_path,
                          default_symlinks_path="symlinks_path",
                          supported_git_protocols="")


def test_symlinks_path():

    default_path = 'resolve_symlinks'

    parser = argparse.ArgumentParser()
    args = ['--foo', '-b']

    options = Options(args=args, parser=parser,
                      default_resolve_path='resolve_path',
                      default_symlinks_path=default_path,
                      supported_git_protocols='')

    assert options.symlinks_path() == default_path

    parser = argparse.ArgumentParser()
    args = ['--foo', '--symlinks_path', '/tmp/symlinks', '-b']

    options = Options(args=args, parser=parser,
                      default_resolve_path='resolve_path',
                      default_symlinks_path=default_path,
                      supported_git_protocols="")

    assert options.symlinks_path() == '/tmp/symlinks'


def test_user_path_to_dependency():

    dependency = mock.Mock()
    dependency.name = 'foo'

    # Path not specified
    parser = argparse.ArgumentParser()
    args = ['--foo', '--resolve_path', '/tmp/bundlehere', '-b']

    options = Options(args=args, parser=parser,
                      default_resolve_path='resolve_path',
                      default_symlinks_path='symlinks_path',
                      supported_git_protocols='')

    options.add_dependency(dependency)

    assert options.path(dependency=dependency) is None

    # Path specified
    parser = argparse.ArgumentParser()
    args = ['--foo', '--resolve_path', '/tmp/bundlehere',
            '--foo_path', '/home/stw/code1', '-b']

    options = Options(args=args, parser=parser,
                      default_resolve_path='resolve_path',
                      default_symlinks_path="symlinks_path",
                      supported_git_protocols="")

    options.add_dependency(dependency)

    assert options.path(dependency=dependency) == '/home/stw/code1'


def test_git_protocol():

    parser = argparse.ArgumentParser()
    args = ['--foo', '-b']

    options = Options(args=args, parser=parser,
                      default_resolve_path='resolve_path',
                      default_symlinks_path="symlinks_path",
                      supported_git_protocols="")

    assert options.git_protocol() is None

    parser = argparse.ArgumentParser()
    args = ['--foo', '--git_protocol', 'myproto://', '-b']

    options = Options(args=args, parser=parser,
                      default_resolve_path='resolve_path',
                      default_symlinks_path="symlinks_path",
                      supported_git_protocols="")

    assert options.git_protocol() == 'myproto://'


def test_fast_resolve():

    parser = argparse.ArgumentParser()
    args = ['--foo', '-b']

    options = Options(args=args, parser=parser,
                      default_resolve_path='resolve_path',
                      default_symlinks_path="symlinks_path",
                      supported_git_protocols="")

    assert options.fast_resolve() is False

    parser = argparse.ArgumentParser()
    args = ['--foo', '--fast_resolve', '-b']

    options = Options(args=args, parser=parser,
                      default_resolve_path='resolve_path',
                      default_symlinks_path="symlinks_path",
                      supported_git_protocols="")

    assert options.fast_resolve() is True


def test_exclusive_lock_options():

    # Test that the two options --lock_paths and --lock_versions
    # are mutually exclusive

    # First ok only --lock_paths
    parser = argparse.ArgumentParser()
    args = ['--lock_paths']

    options = Options(args=args, parser=parser,
                      default_resolve_path='resolve_path',
                      default_symlinks_path="symlinks_path",
                      supported_git_protocols="")

    assert options.lock_paths() is True
    assert options.lock_versions() is False

    # Second ok only --lock_versions
    parser = argparse.ArgumentParser()
    args = ['--lock_versions']

    options = Options(args=args, parser=parser,
                      default_resolve_path='resolve_path',
                      default_symlinks_path="symlinks_path",
                      supported_git_protocols="")

    assert options.lock_paths() is False
    assert options.lock_versions() is True

    # Fail case
    parser = argparse.ArgumentParser()
    args = ['--lock_versions', '--lock_paths']

    with pytest.raises(WurfError):
        options = Options(args=args, parser=parser,
                          default_resolve_path='resolve_path',
                          default_symlinks_path="symlinks_path",
                          supported_git_protocols="")
