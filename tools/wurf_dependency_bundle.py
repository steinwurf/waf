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
from waflib import ConfigSet

import os

OPTIONS_NAME = 'Dependency options'
""" Name of the options group """

DEFAULT_BUNDLE_PATH = 'bundle_dependencies'
""" Default folder to use for bundled dependencies """

DEPENDENCY_PATH_KEY = '%s-path'
""" Key to the dependency paths in the options """

DEPENDENCY_CHECKOUT_KEY = '%s-checkout'
""" Key to the dependency checkouts in the options """

dependencies = dict()
""" Dictionary for storing the dependency information """

dependency_paths = []
""" List to store the dependency paths """

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

    # Skip dependencies that were already resolved
    if name not in dependencies:

        dependencies[name] = resolver

        bundle_opts = conf.opt.get_option_group(OPTIONS_NAME)
        add = bundle_opts.add_option

        add('--%s-path' % name,
            dest=DEPENDENCY_PATH_KEY % name,
            default=False,
            help='Path to %s' % name)

        add('--%s-use-checkout' % name,
            dest=DEPENDENCY_CHECKOUT_KEY % name,
            default=False,
            help='The checkout to use for %s' % name)

        if conf.active_resolvers:
            # Resolve this dependency immediately
            path = resolve_dependency(conf, name)
            # Recurse into this dependency
            conf.recurse([path])


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
        help='The folder where the bundled dependencies are downloaded. '
             'Default folder: "{}"'.format(DEFAULT_BUNDLE_PATH))


def resolve_dependency(conf, name):

    # If the user specified a path for this dependency
    key = DEPENDENCY_PATH_KEY % name
    dependency_path = getattr(conf.options, key, None)

    if dependency_path:

        dependency_path = expand_path(dependency_path)

        conf.start_msg('User resolve dependency %s' % name)
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

    dependency_paths.append(dependency_path)
    return dependency_path


def resolve(ctx):
    """
    The resolve function for the bundle dependency tool
    :param conf: the resolve context
    """
    if ctx.active_resolvers:
        ctx.load('wurf_dependency_resolve')
        ctx.env['DEPENDENCY_PATHS'] = []
    else:
        # Reload the environment from a previously completed resolve step
        try:
            path = os.path.join(ctx.bldnode.abspath(), 'resolve.config.py')
            ctx.env = ConfigSet.ConfigSet(path)
        except EnvironmentError:
            pass


def post_resolve(ctx):
    """
    This function runs after the resolve step is completed
    :param conf: the resolve context
    """
    if ctx.active_resolvers:
        # Save the environment that was created during the active resolve step
        ctx.env['DEPENDENCY_PATHS'] = dependency_paths
        path = os.path.join(ctx.bldnode.abspath(), 'resolve.config.py')
        ctx.env.store(path)
    else:
        # Go through the previously resolved dependencies to fetch the
        # options defined in their resolve functions
        for path in ctx.env['DEPENDENCY_PATHS']:
            ctx.recurse([path])


def configure(conf):
    """
    The configure function for the bundle dependency tool
    :param conf: the configuration context
    """
    conf.env['DEPENDENCY_PATHS'] = dependency_paths
    for path in dependency_paths:
        conf.recurse([path])


def build(bld):

    for path in bld.env['DEPENDENCY_PATHS']:
        bld.recurse([path])
