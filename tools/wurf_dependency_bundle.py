#! /usr/bin/env python
# encoding: utf-8

"""
Waf tool used to track dependencies. Using git tags to track whether a
compatible newer version of a specific library is available. The git
tags must be named after the Semantic Versioning scheme defined here:
www.semver.org

This tool is loaded automatically in "wurf_common_tools".
"""

import os
import sys
import argparse

from waflib.Configure import conf
from waflib import Utils
from waflib import Logs
from waflib import Errors
from waflib import ConfigSet


OPTIONS_NAME = 'Dependency options'
""" Name of the options group """

DEFAULT_BUNDLE_PATH = 'bundle_dependencies'
""" Default folder to use for bundled dependencies """

DEPENDENCY_PATH_KEY = '%s-path'
""" Key to the dependency paths in the options """

DEPENDENCY_CHECKOUT_KEY = '%s-use-checkout'
""" Key to the dependency checkouts in the options """

dependencies = dict()
""" Dictionary that stores the dependency resolvers """

dependency_dict = dict()
""" Dictionary to store and access the dependency paths by name """

dependency_list = []
""" List to store the dependency paths in the order of their definition """


@conf
def add_dependency(ctx, resolver, recursive_resolve=True, optional=False):
    """
    Adds a dependency.
    :param resolver: a resolver object which is responsible for downloading
                     the dependency if necessary
    :param recursive_resolve: specifies if it is allowed to recurse into the
                     dependency wscript after the dependency is resolved
    :param optional: specifies if this dependency is optional (an optional
                     dependency might not be resolved if unavailable)
    """
    name = resolver.name

    if len(dependencies) == 0 and name != 'waf-tools':
        ctx.fatal('waf-tools should be added before other dependencies')

    if name in dependencies:
        if type(resolver) != type(dependencies[name]) or \
           dependencies[name] != resolver:
            ctx.fatal('Incompatible dependency resolvers %r <=> %r '
                       % (resolver, dependencies[name]))

    # Skip dependencies that were already resolved
    #
    # @todo: Should we check here that the dependencies are compatible
    # e.g. for the semver dependency that they have the same major version
    # requirement?
    if name not in dependencies:

        # We store information about a dependency as a dictionary in the
        # context environment
        ctx.env['DEPENDENCY_DICT'][name] = dict()
        ctx.env['DEPENDENCY_DICT'][name]['recurse'] = recursive_resolve

        # ctx.env['DEPENDENCY_LIST'].append({'name':name,'recurse':recursive_resolve})

        dependencies[name] = resolver

        bundle_opts = ctx.opt.get_option_group(OPTIONS_NAME)
        add = bundle_opts.add_option

        add('--%s-path' % name,
            dest=DEPENDENCY_PATH_KEY % name,
            default=None,
            help='Path to %s' % name)

        add('--%s-use-checkout' % name,
            dest=DEPENDENCY_CHECKOUT_KEY % name,
            default=None,
            help='The checkout to use for %s' % name)

        # The dependency resolvers are allowed to download dependencies
        # if this is an "active" resolve step
        if ctx.active_resolvers:
            # Resolve this dependency immediately
            path = resolve_dependency(ctx, name, optional)
            # Recurse into this dependency
            if recursive_resolve and path:
                ctx.recurse([path])
        # Otherwise check if we already stored the path to this dependency
        # when we resolved it (during an "active" resolve step)
        elif name in ctx.env['DEPENDENCY_DICT']:
            path = ctx.env['DEPENDENCY_DICT'][name]['path']
            # Recurse into this dependency
            if recursive_resolve:
                ctx.recurse([path])

@conf
def add_git_semver_dependency(ctx, name, git_repository, major, minor=None,
                              patch=None, recursive_resolve=True,
                              optional=False):
    """
    Adds ResolveVersion dependency (this function exists only such that
    wscripts do not have to perform an import to access the ResolveVersion
    class).

    :param name: the name of this dependency resolver
    :param git_repository: URL of the Git repository where the dependency
                           can be found
    :param major: The major version number to track (ensures binary
                  compatibility), None for newest
    :param minor: The minor version number to track, None for newest
    :param patch: The patch version number to track, None for newest
                  the dependency if necessary
    :param recursive_resolve: specifies if it is allowed to recurse into the
                              dependency wscript after the dependency is
                              resolved
    :param optional: specifies if this dependency is optional (an optional
                     dependency might not be resolved if unavailable)
    """
    import waflib.extras.wurf_dependency_resolve as resolve
    ctx.add_dependency(
        resolve.ResolveVersion(name, git_repository, major, minor, patch),
        recursive_resolve, optional)

@conf
def add_git_commit_dependency(ctx, name, git_repository, commit,
                              recursive_resolve=True, optional=False):
    """
    Adds ResolveVersion dependency (this function exists only such that
    wscripts do not have to perform an import to access the ResolveVersion
    class).

    :param name: the name of this dependency resolver
    :param git_repository: URL of the Git repository where the dependency
                           can be found
    :param major: The major version number to track (ensures binary
                  compatibility), None for newest
    :param minor: The minor version number to track, None for newest
    :param patch: The patch version number to track, None for newest
                  the dependency if necessary
    :param recursive_resolve: specifies if it is allowed to recurse into the
                              dependency wscript after the dependency is
                              resolved
    :param optional: specifies if this dependency is optional (an optional
                     dependency might not be resolved if unavailable)
    """
    import waflib.extras.wurf_dependency_resolve as resolve
    ctx.add_dependency(
        resolve.ResolveGitCommit(name, git_repository, commit),
        recursive_resolve, optional)

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


def resolve_dependency(ctx, name, optional=False):
    # The --%s-path option is parsed directly here, since we want to allow
    # option arguments without the = sign, e.g. --xy-path my-path-to-xy
    # We cannot use ctx.options where --xy-path would be handled as a
    # standalone boolean option (which has no arguments)
    p = argparse.ArgumentParser()
    p.add_argument('--%s-path' % name, dest='dependency_path', type=str)
    args, unknown = p.parse_known_args(args=sys.argv[1:])
    dependency_path = args.dependency_path

    if dependency_path:

        dependency_path = expand_path(dependency_path)

        ctx.start_msg('User resolve dependency %s' % name)
        ctx.end_msg(dependency_path)

    else:
        # Download the dependency to bundle_path

        # Get the path where the bundled dependencies should be placed
        bundle_path = expand_path(ctx.options.bundle_path)
        Utils.check_dir(bundle_path)

        ctx.start_msg('Resolve dependency %s' % name)

        # The --%s-use-checkout option is parsed directly, since we want to
        # allow option arguments without the = sign
        p = argparse.ArgumentParser()
        p.add_argument('--%s-use-checkout' % name, dest='dependency_checkout',
                       type=str)
        args, unknown = p.parse_known_args(args=sys.argv[1:])
        dependency_checkout = args.dependency_checkout

        # Try to resolve this dependency
        try:
            dependency_path = dependencies[name].resolve(
                ctx=ctx,
                path=bundle_path,
                use_checkout=dependency_checkout)
        except Exception as e:
            ctx.to_log('Exception when resolving dependency: {}'.format(name))
            ctx.to_log(e)
            if optional:
                # An optional dependency might be unavailable if the user
                # does not have a license to access the repository, so we just
                # print the status message and continue
                ctx.end_msg('Unavailable', color='RED')
            else:
                # A non-optional dependency must be resolved
                repo_url = dependencies[name].repository_url(ctx, 'https://')
                ctx.fatal('Error: the "{}" dependency is not available. '
                          'Please check that you have a valid Steinwurf '
                          'license and you can access the repository at: '
                          '{}'.format(name, repo_url))
        else:
            ctx.end_msg(dependency_path)

    if dependency_path:
        ctx.env['DEPENDENCY_DICT'][name]['path'] = dependency_path

        dependency_list.append(dependency_path)
    return dependency_path


def resolve(ctx):
    """
    The resolve function for the bundle dependency tool
    :param ctx: the resolve context
    """
    if ctx.active_resolvers:
        # wurf_dependency_resolve and wurf_git are only loaded if this is
        # an "active" resolve step (i.e. if we are configuring the project)
        ctx.load('wurf_dependency_resolve')
        # Create a dictionary to store the resolved dependency paths by name
        ctx.env['DEPENDENCY_DICT'] = dict()
        ctx.env['DEPENDENCY_LIST'] = list()
    else:
        # Reload the environment from a previously completed resolve step
        # if resolve.config.py exists in the build directory
        try:
            path = os.path.join(ctx.bldnode.abspath(), 'resolve.config.py')
            ctx.env = ConfigSet.ConfigSet(path)
        except EnvironmentError:
            pass


def post_resolve(ctx):
    """
    This function runs after the resolve step is completed
    :param ctx: the resolve context
    """
    if ctx.active_resolvers:
        # The dependency_dict will be needed in later steps
        dependency_dict.update(ctx.env['DEPENDENCY_DICT'])
        # Save the environment that was created during the active resolve step
        path = os.path.join(ctx.bldnode.abspath(), 'resolve.config.py')
        ctx.env.store(path)


def configure(conf):
    """
    The configure function for the bundle dependency tool
    :param conf: the configuration context
    """
    # Copy the dependency dict and list (that were filled in the resolve step)
    # to the persistent environment of the real ConfigurationContext
    conf.env['DEPENDENCY_LIST'] = dependency_list
    conf.env['DEPENDENCY_DICT'] = dependency_dict
    # The dependencies will be enumerated in the same order as
    # they were defined in the wscripts (waf-tools must be the first)
    # for path in conf.env['DEPENDENCY_LIST']:
        # conf.recurse([path])

    print(conf.env)

    # The previous code above now commented defines that there must be a
    # certain order in the dependencies, lets try without
    for name,config in conf.env['DEPENDENCY_DICT'].iteritems():
        if config['recurse']:
            conf.recurse(config['path'])


def build(bld):
    # The BuildContext reloads the environment of the ConfigurationContext,
    # so the DEPENDENCY_LIST will be the same, but in the build step we
    # recurse into the dependencies in the reverse order to avoid potential
    # issues with tasks that are defined by a dependency of a dependency.
    # for path in reversed(bld.env['DEPENDENCY_LIST']):
        # bld.recurse([path])

    # The previous code above now commented defines that there must be a
    # certain order in the dependencies, lets try without
    for name,config in conf.env['DEPENDENCY_DICT'].iteritems():
        if config['recurse']:
            conf.recurse(config['path'])


@conf
def has_dependency_path(self, name):
    """
    Returns true if the dependency has been specified
    """
    return name in self.env['DEPENDENCY_DICT']


@conf
def dependency_path(self, name):
    """
    Returns the dependency path
    """
    return self.env['DEPENDENCY_DICT'][name]['path']
