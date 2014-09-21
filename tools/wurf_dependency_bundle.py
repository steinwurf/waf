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

USE_PATH_KEY = 'use_path'
""" Destination of the dependency paths in the options """

USE_CHECKOUT_KEY = 'use_checkout'
""" Destination of the dependency checkouts in the options """

dependencies = dict()
""" Dictionary for storing the dependency information """

toplevel_dependencies = []
""" List to store top-level dependencies """


def add_dependency(conf, resolver):
    """
    Adds a dependency.
    :param resolver: a resolver object which is responsible for downloading
                     the dependency if necessary
    """
    name = resolver.name

    if name in dependencies:
        if type(resolver) != type(dependencies[name]) or \
           dependencies[name] != resolver:
            conf.fatal('Incompatible dependency resolvers %r <=> %r '
                       % (resolver, dependencies[name]))
    else:
        dependencies[name] = resolver
        # Top-level dependencies must be enumerated in the specified order,
        # because waf-tools must be resolved and recursed first to define the
        # necessary tools for the other dependencies
        if conf.is_toplevel():
            toplevel_dependencies.append(name)

    # Top-level dependencies cannot be resolved immediately
    if not conf.is_toplevel():
        # Skip dependencies that were already resolved
        if not name in conf.env['BUNDLE_DEPENDENCIES']:
            # Resolve this dependency defined by another dependency
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

    add('--use-path', default=None, action="append", dest='use_path',
        help='Use manual path to listed dependencies')

    add('--use-checkout', default=None, action="append", dest='use_checkout',
        help='Use specific checkout to listed dependencies')


def parse_options(options_string):
    result = {}
    if options_string:
        for options in options_string:
            for option in options.split(','):
                try:
                    key, value = option.split('=', 1)
                    result[key] = value
                except ValueError:
                    result[option] = True

    return result


def resolve_dependency(conf, name):

    # If the user specified a path for this dependency
    if name in conf.env[USE_PATH_KEY]:

        dependency_path = conf.env[USE_PATH_KEY][name]
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

        dependency_checkout = None

        if name in conf.env[USE_CHECKOUT_KEY]:
            dependency_checkout = conf.env[USE_CHECKOUT_KEY][name]

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

    conf.env[USE_PATH_KEY] = parse_options(conf.options.use_path)
    conf.env[USE_CHECKOUT_KEY] = parse_options(conf.options.use_checkout)

    conf.env['BUNDLE_DEPENDENCIES'] = dict()

    # Enumerate the top-level dependencies defined in the project's wscript
    # These dependencies might include their own dependencies in the process
    for dependency in toplevel_dependencies:

        resolve_dependency(conf, dependency)
        conf.recurse_helper(dependency)


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
