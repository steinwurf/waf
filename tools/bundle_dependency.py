#! /usr/bin/env python
# encoding: utf-8

"""
Waf tool used to track dependencies. Using git tags to track whether a
compatible newer version of a specific library is available. The git
tags must be named after the Semantic Versioning scheme defined here
www.semver.org

The wscript will look like this:

def options(opt):
    opt.load('bundle_dependencies')

def configure(conf):
    conf.load('bundle_dependencies')


"""

from waflib.Configure import conf
from waflib.Configure import ConfigurationContext
from waflib.Options import OptionsContext
from waflib.ConfigSet import ConfigSet

import waflib.Options as Opt

from waflib import Logs
from waflib import Options
from waflib import Utils
from waflib import Scripting
from waflib import Context
from waflib import Errors

import sys
import os
import shutil

import semver

OPTIONS_NAME = 'Dependency options'
""" Name of the options group """

DEFAULT_BUNDLE_PATH = 'bundle_dependencies'
""" Default folder to use for bundled dependencies """

DEPENDENCY_PATH_KEY = '%s_DEPENDENCY_PATH'
""" Destination of the dependency paths in the options """

dependencies = dict()
""" Dictionary storing the dependency information """

def add_dependency(name, repo_url, semver):
    """
    Adds a dependency. The dependency will la
    :param name: the name / identifier for this dependency
    :param repo_url: the url to the git repository where the dependency
                     may be fetched
    :param tag: the major version to track
    """

    if name in dependencies:
        dep = dependencies[name]

        # check that the existing dependency specifies
        # the same tag

        if tag !=  dep['tag']:
            raise Errors.WafError('Existing dependency %s tag '
                                  'mismatch %s <=> %s' %
                                  (name, tag, dep['tag']))

        if repo_url != dep['repo_url']:
            raise Errors.WafError('Exising dependency %s repo_url '
                                  'mismatch %s <=> %s' %
                                  (name, repo_url, dep['repo_url']))

    else:

        dependencies[name] = dict()
        dependencies[name]['tag'] = tag
        dependencies[name]['repo_url'] = repo_url



def expand_path(path):
    """
    Simple helper to expand paths
    :param path: a directory path to be expanded
    :return: the expanded path
    """
    return os.path.abspath(os.path.expanduser(path))


def options(opt):
    """
    Adds the options needed to control dependencies to the
    options context. Options are shown when ./waf -h is invoked
    :param opt: the Waf OptionsContext
    """

    opt.load('git')

    bundle_opts = opt.add_option_group(OPTIONS_NAME)

    add = bundle_opts.add_option

    add('--bundle', default=False, dest='bundle',
        help="Which dependencies to bundle")

    add('--bundle-path', default=DEFAULT_BUNDLE_PATH, dest='bundle_path',
        help="The folder used for downloaded dependencies")

    add('--bundle-options', dest='bundle_options', default=False,
        action='store_true', help='List dependencies which may be bundled')

    add('--bundle-show', dest='bundle_show', default=False,
        action='store_true', help='Show the dependency bundle options')

    for d in dependencies:
        add('--%s-path' % d, dest = DEPENDENCY_PATH_KEY % d, default=False,
            help='path to %s' % d)

def configure(conf):
    """
    The configure function for the bundle dependency tool
    :param conf: the configuration context
    """

    conf.load('git')

    conf.env['BUNDLE_PATH'] = expand_path(conf.options.bundle_path)

    # List all the dependencies to be bundled
    bundle_list = expand_bundle(conf.options.bundle)

    # Loop over all dependencies and fetch the ones
    # specified using the bundle command
    for name in bundle_list:
        path = conf.fetch_git_dependency(name)

        key = DEPENDENCY_PATH_KEY % name
        conf.env[key] = expand_path(path)

    # Loop over the remaining dependencies and check
    # if they have a path specified
    remaining = list(set(dependencies.keys()) - set(bundle_list))

    for name in remaining:
        key = DEPENDENCY_PATH_KEY % name
        path = getattr(conf.options, key)

        if path: conf.env[key] = expand_path(path)



def expand_bundle(arg):
    """
    Expands the bundle arg so that e.g. 'ALL,-gtest' becomes the
    right set of dependencies
    """
    if not arg:
        return []

    arg = arg.split(',')

    if 'NONE' in arg and 'ALL' in arg:
        self.fatal('Cannot specify both ALL and NONE as dependencies')

    candidate_score = dict([(name, 0) for name in dependencies])

    def check_candidate(c):
        if c not in candidate_score:
            self.fatal('Cannot bundle %s, since it is not specified as a'
                       ' dependency' % c)

    for a in arg:

        if a == 'ALL':
            for candidate in candidate_score:
                candidate_score[candidate] += 1
            continue

        if a == 'NONE':
            continue

        if a.startswith('-'):
            a = a[1:]
            check_candidate(a)
            candidate_score[a] -= 1

        else:
            check_candidate(a)
            candidate_score[a] += 1

    candidates = [name for name in candidate_score if candidate_score[name] > 0]
    return candidates


@conf
def fetch_git_dependency(self, name):

    dep = dependencies[name]

    tag = dep['tag']
    repo_url = dep['repo_url']

    dep_dir = name

    if tag:
        dep_dir = dep_dir + '-' + tag

    repo_dir = os.path.join(self.env['BUNDLE_PATH'], dep_dir)

    if not repo_dir:
        self.fatal('Trying to load dependency %s which is not'
                   ' bundled or has a path' % name)

    if os.path.isdir(repo_dir):

        # if we do not have a tag means we are following the
        # master -- ensure we have the newest by doing a pull
        Logs.debug('%s dir already exists skipping git clone' % repo_dir)

        if not tag:
            self.git_pull(repo_dir, quiet = True)

    else:

        Utils.check_dir(self.env['BUNDLE_PATH'])
        self.repository_clone(repo_dir, repo_url)

        if tag:
            self.git_checkout(repo_dir, tag)

    if self.git_has_submodules(repo_dir):
        self.git_submodule_init(repo_dir)
        self.git_submodule_update(repo_dir)


    return repo_dir


@conf
def has_dependency_path(self, name):
    """
    Returns true if the dependency has been specified
    """
    key = DEPENDENCY_PATH_KEY % name

    if key in self.env:
        return True

    return False


@conf
def dependency_path(self, name):
    """
    Returns the dependency path
    """
    key = DEPENDENCY_PATH_KEY % name

    return self.env[key]










