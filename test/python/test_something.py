import os
import sys
import subprocess
import glob
import time
import mock
import functools

import wurf_git
import wurf_git_url_resolver
import wurf_git_resolver

def test_copy_file(test_directory):
    test_directory.copy_files('test/prog1/*')
    test_directory.copy_file('build/*/waf')

    r = test_directory.run('python','waf','configure')

    assert r.returncode == 0
    assert r.stdout.match('*finished successfully*')

    r = test_directory.run('python', 'waf', 'build')

    assert r.returncode == 0

def build_git_resolver(registery):
    git = registery.build('git')
    url_resolver = registery.build('git_url_resolver')
    log = registery.build('log')

    return wurf_git_resolver.WurfGitResolver(
        git=git, url_resolver=url_resolver, log=log)

def build_source_resolver(registery):

    source_resolvers = {'git': registery.build('git_resolver')}

    log = registery.build('log')

    return wurf_source_resolver.WurfSourceResolver(
        source_resolvers=source_resolvers, log=log)


def test_working_on_it(test_directory):

    class Registery(object):

        def __init__(self):
            self.registery = {}

        def register(self, obj, factory):
            self.registery[obj] = factory

        def build(self, obj):
            factory = self.registery[obj]
            return factory(self)

    dep = {"name":"waf", "patches": ["patches/patch01.patch",
           "patches/patch02.patch"], "optional":True,
           "sources":[{"resolver":"git", "url":"gitrepo.git"}]}

    ctx = mock.Mock()
    log = mock.Mock()
    binary = '/bin/git'
    cwd = '/tmp'
    name = dep['name']

    registery = Registery()
    registery.register("git",
        lambda r: wurf_git.WurfGit(binary, ctx))

    registery.register('git_url_resolver',
        lambda r: wurf_git_url_resolver.WurfGitUrlResolver())

    registery.register('log', lambda r: log)

    registery.register('git_resolver', build_git_resolver)


    build_function = wurf_source_resolver.WurfSourceResolver.build
    reg.register('source_resolver',
        functools.partial(build_function, dependency=dep))


    f = reg.build('source_resolver')
    #assert(f.color() == "red")
