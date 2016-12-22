#!/usr/bin/env python
# encoding: utf-8

import shutilwhich

def test_add_dependency(test_directory):
    """ Integration testing of adding a dependency."""

    #app_dir = test_directory.mkdir('app')

    app_dir = test_directory.copy_dir(directory='test/test_add_dependency/app')
    app_dir.copy_file('build/waf')

    # Make a directory where we place the libraries that we would have cloned
    # if we had use the full waf resolve functionality.
    #
    # To avoid relying on network connectivity we simply place the
    # libraries there and then fake the git clone step.
    git_dir = test_directory.mkdir(directory='git_dir')

    foo_dir = git_dir.copy_dir(directory='test/test_add_dependency/libfoo')
    foo_dir.run('git', 'init')
    foo_dir.run('git', 'add', '.')

    # We cannot commit without setting a user + email, but that is not always
    # available. So we can set it just for the one commit command using this
    # approach: http://stackoverflow.com/a/22058263/1717320
    #
    foo_dir.run('git', '-c', 'user.name=John', '-c', 'user.email=doe@email.org', 'commit', '-m', 'oki')
    foo_dir.run('git', 'tag', '1.3.3.7')

    # The bundle_dependencies directory is the default, so when we do
    # configure without any arguments dependencies are expected to be
    # placed there.

    #git_binary = shutilwhich.which('git')

    #libfoo_repo = test

    #bundle_directory = test_directory.mkdir('bundle_dependencies')


    #bundle_directory.copy_dir('test/test_add_dependency/libfoo')

    ##libfoo_directory = bundle_directory.mkdir('libbar-h4sh')
    #libfoo_directory.copy_dir('test/test_add_dependency/libbar')

    app_dir.run('python', 'waf', 'configure', '-v')
    app_dir.run('python', 'waf', 'build', '-v')


    # r = test_directory.run('python', 'waf', 'configure', '-v', '--waf-use-checkout=waf-1.9.4')
    #
    # assert r.returncode == 0, str(r)
    #
    # r = test_directory.run('python', 'waf', 'build', '-v')
    #
    # assert r.returncode == 0, str(r)
    #
    # r = test_directory.run('python', 'waf', 'configure', '-v', '--waf-path=/tmp')
    #
    # assert r.returncode == 0, str(r)
    #
    # r = test_directory.run('python', 'waf', 'build', '-v')
    #
    # assert r.returncode == 0, str(r)
    #
    # r = test_directory.run('python', 'waf', 'configure', '-v', '--bundle-path=okidoki')
    #
    # assert r.returncode == 0, str(r)
    #
    # r = test_directory.run('python', 'waf', 'build', '-v')
    #
    # assert r.returncode == 0, str(r)
    #

    #print(str(r))
