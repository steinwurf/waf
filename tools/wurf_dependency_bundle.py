#! /usr/bin/env python
# encoding: utf-8

"""
Waf tool used to track dependencies. Using git tags to track whether a
compatible newer version of a specific library is available. The git
tags must be named after the Semantic Versioning scheme defined here:
www.semver.org

The wscript will look like this:

def options(opt):
    opt.load('wurf_dependency_bundle')

def configure(conf):
    conf.load('wurf_dependency_bundle')

"""

from waflib.Configure import conf
from waflib import Utils
from waflib import Errors

import os

OPTIONS_NAME = 'dependency options'
""" Name of the options group """

DEFAULT_BUNDLE_PATH = 'bundle_dependencies'
""" Default folder to use for bundled dependencies """

DEPENDENCY_PATH_KEY = '%s-path'
""" Key to the dependency paths in the options """

DEPENDENCY_CHECKOUT_KEY = '%s-checkout'
""" Key to the dependency checkouts in the options """

dependencies = dict()
""" Dictionary for storing the dependency information """


@conf
def add_dependency(conf, resolver):
    """
    Adds a dependency.
    :param resolver: a resolver object which is responsible for downloading
                     the dependency if necessary
    """
    name = resolver.name

    if len(dependencies) == 0 and name != 'waf-tools':
        conf.fatal('waf-tools should be added before other dependencies')

    if name in dependencies:
        if type(resolver) != type(dependencies[name]) or \
           dependencies[name] != resolver:
            conf.fatal('Incompatible dependency resolvers %r <=> %r '
                       % (resolver, dependencies[name]))
    else:
        dependencies[name] = resolver

        # Skip dependencies that were already resolved
        if not name in conf.env['BUNDLE_DEPENDENCIES']:
            # Resolve this dependency immediately
            resolve_dependency(conf, name)
            # Recurse into this dependency
            conf.recurse_helper(name)


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
    opt.load('wurf_dependency_resolve')

    bundle_opts = opt.add_option_group(OPTIONS_NAME)

    add = bundle_opts.add_option

    add('--bundle-path', default=DEFAULT_BUNDLE_PATH, dest='bundle_path',
        help="The folder used for downloaded dependencies")


def resolve_dependency(conf, name):

    # If the user specified a path for this dependency
    key = DEPENDENCY_PATH_KEY % name
    dependency_path = getattr(conf.options, key, None)

    if dependency_path:

        dependency_path = expand_path(dependency_path)

        conf.start_msg('User resolve dependency %s' % name)
        conf.env['BUNDLE_DEPENDENCIES'][name] = dependency_path
        conf.end_msg(dependency_path)

    else:
        # Download the dependency to bundle_path

        # Get the path where the bundled dependencies should be placed
        bundle_path = expand_path(conf.options.bundle_path)
        Utils.check_dir(bundle_path)

        conf.start_msg('Resolve dependency %s' % name)

        key = DEPENDENCY_CHECKOUT_KEY % name
        dependency_checkout = getattr(conf.options, key, None)

        dependency_path = dependencies[name].resolve(
            ctx=conf,
            path=bundle_path,
            use_checkout=dependency_checkout)

        conf.end_msg(dependency_path)

        conf.env['BUNDLE_DEPENDENCIES'][name] = dependency_path


def configure(conf):
    """
    The configure function for the bundle dependency tool
    :param conf: the configuration context
    """
    conf.load('wurf_dependency_resolve')

    conf.env['BUNDLE_DEPENDENCIES'] = dict()


def build(bld):

    for dependency in bld.env['BUNDLE_DEPENDENCIES']:
        bld.recurse_helper(dependency)


@conf
def has_dependency_path(self, name):
    """
    Returns true if the dependency has been specified
    """

    if name in self.env['BUNDLE_DEPENDENCIES']:
        return True

    return False


@conf
def dependency_path(self, name):
    """
    Returns the dependency path
    """
    return self.env['BUNDLE_DEPENDENCIES'][name]


@conf
def is_toplevel(self):
    """
    Returns true if the current script is the top-level wscript
    """
    return self.srcnode == self.path


@conf
def recurse_helper(self, name):
    if not self.has_dependency_path(name):
        self.fatal('Load a tool to find %s as system dependency' % name)
    else:
        p = self.dependency_path(name)
        # Some projects might not have a wscript file in their root folder
        if os.path.isfile(os.path.join(p, 'wscript')):
            self.recurse([p])
