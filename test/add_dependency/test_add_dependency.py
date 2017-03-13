#!/usr/bin/env python
# encoding: utf-8

import os
import json

""" Integration testing of adding a dependency.

This test is a bit involved so lets try to explain what it does:

We are setting up the following dependency graph:

           +--------------+
           |     app      |
           +---+------+---+
               |      |
               |      |
      +--------+      +-------+
      |                       |
      v                       v
+-----+------+          +-----+-----+
|  libfoo    |          |  libbaz   |
+-----+------+          +-----+-----+
      |                       ^
      v                       |
+-----+------+                |
|  libbar    |----------------+
+------------+

The arrows indicate dependencies, so:

- 'app' depends on 'libfoo' and 'libbaz'
- 'libfoo' depends on 'libbar'
- 'libbar' depends on 'libbaz'

"""

def mkdir_app(directory):
    app_dir = directory.mkdir('app')
    app_dir.copy_file('test/add_dependency/app/main.cpp')
    app_dir.copy_file('test/add_dependency/app/wscript')

    app_dir.copy_file('test/add_dependency/fake_git_clone.py')
    app_dir.copy_file('build/waf')
    # Note: waf will call "git config --get remote.origin.url" in this folder,
    # so "git init" is required if the pytest temp folder is located within
    # the main waf folder
    app_dir.run('git', 'init')

    return app_dir


def mkdir_app_json(directory):
    app_dir = directory.mkdir('app')
    app_dir.copy_file('test/add_dependency/app/main.cpp')
    app_dir.copy_file('test/add_dependency/app/wscript_json',
        rename_as='wscript')
    app_dir.copy_file('test/add_dependency/app/resolve.json')

    app_dir.copy_file('test/add_dependency/fake_git_clone.py')
    app_dir.copy_file('build/waf')
    # Note: waf will call "git config --get remote.origin.url" in this folder,
    # so "git init" is required if the pytest temp folder is located within
    # the main waf folder
    app_dir.run('git', 'init')

    return app_dir


def mkdir_libfoo(directory):

    # Add foo dir
    foo_dir = directory.mkdir('libfoo')
    foo_dir.copy_file('test/add_dependency/libfoo/wscript')
    foo_dir.copy_file('test/add_dependency/libfoo/some_repos_contain')
    foo_dir.copy_dir(directory='test/add_dependency/libfoo/src')
    foo_dir.run('git', 'init')
    foo_dir.run('git', 'add', '.')

    # We cannot commit without setting a user + email, but that is not always
    # available. So we can set it just for the one commit command using this
    # approach: http://stackoverflow.com/a/22058263/1717320
    foo_dir.run('git', '-c', 'user.name=John', '-c',
                'user.email=doe@email.org', 'commit', '-m', 'oki')
    foo_dir.run('git', 'tag', '1.3.3.7')
    return foo_dir

def mkdir_libfoo_json(directory):

    # Add foo dir
    foo_dir = directory.mkdir('libfoo')
    foo_dir.copy_file('test/add_dependency/libfoo/wscript_json',
        rename_as='wscript')
    foo_dir.copy_file('test/add_dependency/libfoo/some_repos_contain')
    foo_dir.copy_file('test/add_dependency/libfoo/resolve.json')
    foo_dir.copy_dir(directory='test/add_dependency/libfoo/src')
    foo_dir.run('git', 'init')
    foo_dir.run('git', 'add', '.')

    # We cannot commit without setting a user + email, but that is not always
    # available. So we can set it just for the one commit command using this
    # approach: http://stackoverflow.com/a/22058263/1717320
    foo_dir.run('git', '-c', 'user.name=John', '-c',
                'user.email=doe@email.org', 'commit', '-m', 'oki')
    foo_dir.run('git', 'tag', '1.3.3.7')
    return foo_dir


def mkdir_libbar(directory):

    # Add bar dir
    bar_dir = directory.copy_dir(directory='test/add_dependency/libbar')
    bar_dir.run('git', 'init')
    bar_dir.run('git', 'add', '.')
    bar_dir.run('git', '-c', 'user.name=John', '-c',
                'user.email=doe@email.org', 'commit', '-m', 'oki')
    bar_dir.run('git', 'tag', 'someh4sh')
    return bar_dir


def mkdir_libbaz(directory):

    # Add baz dir
    baz_dir = directory.copy_dir(directory='test/add_dependency/libbaz')
    baz_dir.run('git', 'init')
    baz_dir.run('git', 'add', '.')
    baz_dir.run('git', '-c', 'user.name=John', '-c',
                'user.email=doe@email.org', 'commit', '-m', 'oki')
    baz_dir.run('git', 'tag', '3.1.2')
    baz_dir.run('git', 'tag', '3.2.0')
    baz_dir.run('git', 'tag', '3.3.0')
    baz_dir.run('git', 'tag', '3.3.1')

    return baz_dir

def test_resolve_json(test_directory):
    """ Tests that dependencies declared in the wscript works. I.e. where we
        call add_dependency(...) in the resolve function of the wscript.
    """

    app_dir = mkdir_app_json(directory=test_directory)

    # Make a directory where we place the libraries that we would have cloned
    # if we had use the full waf resolve functionality.
    #
    # To avoid relying on network connectivity we simply place the
    # libraries there and then fake the git clone step.
    git_dir = test_directory.mkdir(directory='git_dir')

    foo_dir = mkdir_libfoo_json(directory=git_dir)
    bar_dir = mkdir_libbar(directory=git_dir)
    baz_dir = mkdir_libbaz(directory=git_dir)

    # Instead of doing an actual Git clone - we fake it and use the paths in
    # this mapping
    clone_path = {
        'github.com/acme-corp/foo.git': foo_dir.path(),
        'gitlab.com/acme-corp/bar.git': bar_dir.path(),
        'gitlab.com/acme/baz.git': baz_dir.path() }

    json_path = os.path.join(app_dir.path(), 'clone_path.json')

    with open(json_path, 'w') as json_file:
        json.dump(clone_path, json_file)

    # Note that waf "climbs" directories to find a lock file in higher
    # directories, and this test is executed within a subfolder of the
    # project's main folder (that already has a lock file). To prevent this
    # behavior, we need to invoke help with the NOCLIMB variable.
    env = dict(os.environ)
    env['NOCLIMB'] = '1'
    app_dir.run('python', 'waf', '--help', env=env)
    app_dir.run('python', 'waf', 'configure', '-v')

    # The symlinks should be available to all dependencies
    assert os.path.exists(os.path.join(app_dir.path(), 'build_symlinks', 'foo'))
    assert os.path.exists(os.path.join(app_dir.path(), 'build_symlinks', 'baz'))
    assert os.path.exists(os.path.join(app_dir.path(), 'build_symlinks', 'bar'))

    app_dir.run('python', 'waf', 'build', '-v')
    app_dir.run('python', 'waf', 'configure', '-v', '--fast-resolve')
    app_dir.run('python', 'waf', 'build', '-v')

    # Test the --lock_versions options
    app_dir.run('python', 'waf', 'configure', '-v', '--lock_versions')
    assert app_dir.contains_file('lock_resolve.json')
    app_dir.run('python', 'waf', 'build', '-v')
    app_dir.run('python', 'waf', 'configure', '-v')
    app_dir.run('python', 'waf', 'build', '-v')

    app_dir.rmfile('lock_resolve.json')

    # Test the --lock_paths options
    app_dir.run('python', 'waf', 'configure', '-v', '--lock_paths')
    assert app_dir.contains_file('lock_resolve.json')

    # Now we can delete the git folders - as we should be able to configure
    # from the frozen dependencies
    #git_dir.rmdir()

    #app_dir.run('python', 'waf', 'configure', '-v')


def test_add_dependency(test_directory):
    """ Tests that dependencies declared in the wscript works. I.e. where we
        call add_dependency(...) in the resolve function of the wscript.
    """

    app_dir = mkdir_app(directory=test_directory)

    # Make a directory where we place the libraries that we would have cloned
    # if we had use the full waf resolve functionality.
    #
    # To avoid relying on network connectivity we simply place the
    # libraries there and then fake the git clone step.
    git_dir = test_directory.mkdir(directory='git_dir')

    foo_dir = mkdir_libfoo(directory=git_dir)
    bar_dir = mkdir_libbar(directory=git_dir)
    baz_dir = mkdir_libbaz(directory=git_dir)

    # Instead of doing an actual Git clone - we fake it and use the paths in
    # this mapping
    clone_path = {
        'github.com/acme-corp/foo.git': foo_dir.path(),
        'gitlab.com/acme-corp/bar.git': bar_dir.path(),
        'gitlab.com/acme/baz.git': baz_dir.path() }

    json_path = os.path.join(app_dir.path(), 'clone_path.json')

    with open(json_path, 'w') as json_file:
        json.dump(clone_path, json_file)

    # Note that waf "climbs" directories to find a lock file in higher
    # directories, and this test is executed within a subfolder of the
    # project's main folder (that already has a lock file). To prevent this
    # behavior, we need to invoke help with the NOCLIMB variable.
    env = dict(os.environ)
    env['NOCLIMB'] = '1'
    app_dir.run('python', 'waf', '--help', env=env)
    app_dir.run('python', 'waf', 'configure', '-v')

    # The symlinks should be available to all dependencies
    assert os.path.exists(os.path.join(app_dir.path(), 'build_symlinks', 'foo'))
    assert os.path.exists(os.path.join(app_dir.path(), 'build_symlinks', 'baz'))
    assert os.path.exists(os.path.join(app_dir.path(), 'build_symlinks', 'bar'))

    app_dir.run('python', 'waf', 'build', '-v')
    app_dir.run('python', 'waf', 'configure', '-v', '--fast-resolve')
    app_dir.run('python', 'waf', 'build', '-v')


def test_add_dependency_path(test_directory):

    app_dir = mkdir_app(directory=test_directory)

    git_dir = test_directory.mkdir(directory='git_dir')

    foo_dir = mkdir_libfoo(directory=git_dir)
    bar_dir = mkdir_libbar(directory=git_dir)

    # Instead of doing an actual Git clone - we fake it and use the paths in
    # this mapping
    clone_path = {
        'github.com/acme-corp/foo.git': foo_dir.path(),
        'gitlab.com/acme-corp/bar.git': bar_dir.path() }

    json_path = os.path.join(app_dir.path(), 'clone_path.json')

    with open(json_path, 'w') as json_file:
        json.dump(clone_path, json_file)

    # Test the --baz-path option: by not putting this dependency in the
    # git_dir, we make sure that our fake git clone step in the wscript
    # cannot find it. Therefore the test will fail if it tries to clone baz.
    path_test = test_directory.mkdir(directory='path_test')
    baz_dir = mkdir_libbaz(directory=path_test)

    app_dir.run('python', 'waf', 'configure', '-v', '--baz-path={}'.format(
                baz_dir.path()))

    # The symlinks should be available to all dependencies
    assert os.path.exists(os.path.join(app_dir.path(), 'build_symlinks', 'foo'))
    assert os.path.exists(os.path.join(app_dir.path(), 'build_symlinks', 'baz'))
    assert os.path.exists(os.path.join(app_dir.path(), 'build_symlinks', 'bar'))

    app_dir.run('python', 'waf', 'build', '-v')
    app_dir.run('python', 'waf', 'configure', '-v', '--fast-resolve')
