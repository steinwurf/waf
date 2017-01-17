#! /usr/bin/env python
# encoding: utf-8

import argparse
import os

from . import wurf_git

from . import wurf_git_semver_resolver
from . import wurf_git_resolver

from . import wurf_user_checkout_resolver
from . import wurf_user_path_resolver
from .dependency_manager import DependencyManager
from .on_active_store_path_resolver import OnActiveStorePathResolver
from .on_passive_load_path_resolver import OnPassiveLoadPathResolver
from .try_resolver import TryResolver
from .git_checkout_resolver import GitCheckoutResolver
from .git_url_parser import GitUrlParser
from .git_url_rewriter import GitUrlRewriter

from . import git_url_rewriter

from . import wurf_error

class WurfProvideRegistryError(wurf_error.WurfError):
    """Generic exception for wurf"""
    def __init__(self, name):

        self.name = name

        super(WurfProvideRegistryError, self).__init__(
            "Fatal error {} alredy added to registry".format(self.name))

class Registry(object):

    # Dictionary containing the provider functions registered
    # using the @provide decorator
    providers = {}

    def __init__(self, use_providers=True):
        """
        :param use_providers: True if the class providers should be added. False
            will create a new Registry instance without any added providers.
        """
        self.registry = {}

        if not use_providers:
            return

        for k,v in Registry.providers.items():
            self.provide(k,v)

    def provide(self, feature, provider, override=False):
        """
        :param feature: The name of the feature as a string
        :param provider: Function to call while will provide the "feature"
        :param override: Determines whether the provider should override an
            existing providers. True of we will override an existing provider for
            the same feature.
        """

        if not override and feature in self.registry:
            raise WurfProvideRegistryError(feature)

        def call(**kwargs):
            return provider(registry=self, **kwargs)

        self.registry[feature] = call

    def provide_value(self, feature, value):

        def call(): return value
        self.registry[feature] = call

    def require(self, feature, **kwargs):
        call = self.registry[feature]
        return call(**kwargs)

    def __contains__(self, key):
        return key in self.registry

def provide(func):

    if func.__name__ in Registry.providers:
        raise WurfProvideRegistryError(func.__name__)
    Registry.providers[func.__name__] = func


@provide
def git_url_parser(registry):

    # We cache the GitUrlParser() object since then we can reuse the regexp
    # used for parsing
    cached = 'cached_git_url_parser'

    if not cached in registry:
        registry.provide_value(cached, GitUrlParser())

    return registry.require(cached)

@provide
def git_url_resolver(registry):
    parser = registry.require('git_url_parser')

    git_protocol = registry.require('git_protocol')

    return GitUrlRewriter(parser=parser)

@provide
def git_url_rewriter(registry):
    parser = registry.require('git_url_parser')

    git_protocol = registry.require('git_protocol')

    return GitUrlRewriter(parser=parser, )

@provide
def user_git_protocol(registry):

    # Cache the result for later lookup
    cached = 'cached_user_git_protocol'

    if cached in registry:
        return registry.require(cached)

    # We support the protocols we know how to rewrite
    supported_protocols = git_url_rewriter.git_protocols.keys()

    # Check if the user specified a git protocol to use:
    parser = registry.require('parser')
    args = registry.require('args')
    ctx = registry.require('ctx')

    parser.add_argument('--git-protocol',
        help='Use a specific git protocol to download dependencies.'
             'Supported protocols {}'.format(supported_protocols))

    known_args, unknown_args = parser.parse_known_args(args=args)

    protocol = known_args.git_protocol

    if protocol and protocol not in supported:
        ctx.fatal('Unknown git protocol specified: "{}", supported '
                  'protocols are {}'.format(protocol, supported_protocols))

    registry.provide_value(cached, protocol)
    return protocol

@provide
def project_git_protocol(registry):

    # Cache the result for later lookup
    cached = 'cached_project_git_protocol'

    if cached in registry:
        return registry.require(cached)

    # We support the protocols we know how to rewrite
    supported_protocols = git_url_rewriter.git_protocols.keys()

    # Try to use the same protocol as the parent project
    git = registry.require('git')
    ctx = registry.require('ctx')
    parser = registry.require('git_url_parser')

    try:
        parent_url = git.remote_origin_url(cwd=os.getcwd())

    except Exception as e:

        ctx.to_log('Exception when executing git.remote_origin_url {}'.format(e))
        registry.provide_value(cached, None)
        return None

    else:

        url = parser.parse(parent_url)
        registry.provide_value(cached, url.protocol)
        return url.protocol


@provide
def git_protocol(registry):

    # Cache the result for later lookup
    cached = 'cached_git_protocol'

    if cached in registry:
        return registry.require(cached)

    # We support the protocols we know how to rewrite
    supported = git_url_rewriter.git_protocols.keys()

    # Check if the user specified a git protocol to use:
    protocol = registry.require('user_git_protocol')

    if not protocol:
        protocol = registry.require('project_git_protocol')

    if not protocol:
        protocol = 'https://'

    # Finally just use https
    registry.provide_value(cached, 'https://')
    return 'https://'



@provide
def bundle_path(registry):
    """ Provides the user path to a specific dependency.

    :param registry: A Registry instance
    :param name: The name of a dependency as a string
    """

    key = 'cached_bundle_path'

    if key in registry:
        return registry.require(key)

    parser = registry.require('parser')
    args = registry.require('args')
    default_bundle_path = registry.require('default_bundle_path')
    utils = registry.require('utils')

    # Using the %default placeholder:
    #    http://stackoverflow.com/a/1254491/1717320
    parser.add_argument('--bundle-path',
        default=default_bundle_path,
        dest='bundle_path',
        help='The folder where the bundled dependencies are downloaded.'
             '(default: %(default)s)')

    known_args, unknown_args = parser.parse_known_args(args=args)

    # The waflib.Utils.check_dir function will ensure that the directory
    # exists
    utils.check_dir(path=known_args.bundle_path)

    registry.provide_value(key, known_args.bundle_path)

    return known_args.bundle_path


@provide
def user_path(registry, dependency):
    """ Provides the user path to a specific dependency.

    :param registry: A Registry instance
    :param dependency: A WurfDependency instance.
    """

    key = 'cached_{}_user_path'.format(dependency.name)

    if key in registry:
        return registry.require(key)

    parser = registry.require('parser')
    args = registry.require('args')

    option = '--%s-path' % dependency.name

    parser.add_argument(option,
        nargs='?',
        dest=option,
        help='Manually specify path for {}.'.format(dependency.name))

    known_args, unknown_args = parser.parse_known_args(args=args)

    # Access the attribute as a dict:
    # https://docs.python.org/3/library/argparse.html#the-namespace-object
    arguments = vars(known_args)

    # Cache the value in the registry
    registry.provide_value(key, arguments[option])

    return arguments[option]

@provide
def user_path_resolver(registry, dependency):

    path = registry.require('user_path', dependency=dependency)

    return wurf_user_path_resolver.WurfUserPathResolver2(path=path)

@provide
def git_sources(registry, dependency):
    """ Takes the dependency sources and re-writes the with the desired protocol

    :param registry: A Registry instance.
    :param dependency: A WurfDependency instance.
    """
    url_resolver = registry.require('git_url_rewriter')


@provide
def git_resolvers(registry, dependency):
    """ Builds a WurfGitResolver instance.

    :param registry: A Registry instance.
    :param dependency: A WurfDependency instance.
    """

    git = registry.require('git')
    url_resolver = registry.require('git_url_resolver')
    ctx = registry.require('ctx')
    bundle_path = registry.require('bundle_path')

    name = dependency.name
    sources = dependency.sources

    def new_resolver(source):
        return wurf_git_resolver.GitResolver(
            git=git, url_resolver=url_resolver, ctx=ctx, name=name,
            bundle_path=bundle_path, source=source)

    resolvers = [new_resolver(source) for source in sources]
    return resolvers


@provide
def git_checkout_resolvers(registry, dependency):
    """ Builds a WurfGitCheckoutResolver instance.

    :param registry: A Registry instance.
    :param dependency: A WurfDependency instance.
    """

    git = registry.require('git')
    ctx = registry.require('ctx')
    git_resolvers = registry.require('git_resolvers',
        dependency=dependency)
    bundle_path = registry.require('bundle_path')

    name = dependency.name
    checkout = dependency.checkout

    def new_resolver(git_resolver):
        return GitCheckoutResolver(git=git, git_resolver=git_resolver, ctx=ctx,
            name=name, bundle_path=bundle_path, checkout=checkout)

    resolvers = [new_resolver(git_resolver) for git_resolver in git_resolvers]
    return resolvers


@provide
def git_source_resolvers(registry, dependency):
    """ Builds git resolvers

    :param registry: A Registry instance.
    :param dependency: A WurfDependency instance.
    """

    method = dependency.method
    method_key = "git_{}_resolvers".format(method)

    return registry.require(method_key, dependency=dependency)

@provide
def passive_path_resolver(registry, dependency):
    """ Builds a WurfPassivePathResolver instance.

    :param registry: A Registry instance.
    """

    ctx = registry.require('ctx')
    bundle_config_path = registry.require('bundle_config_path')
    active_resolve = registry.require('active_resolve')

    name = dependency.name
    sha1 = dependency.sha1

    return OnPassiveLoadPathResolver(ctx=ctx, name=name, sha1=sha1,
        active_resolve=active_resolve, bundle_config_path=bundle_config_path)


@provide
def dependency_resolver(registry, dependency):
    """ Builds a WurfSourceResolver instance."""

    active_resolve = registry.require('active_resolve')
    bundle_config_path = registry.require('bundle_config_path')

    user_resolvers = [
        registry.require('user_path_resolver', dependency=dependency),
        registry.require('passive_path_resolver', dependency=dependency)]

    resolver_key = "{}_source_resolvers".format(dependency.resolver)

    source_resolvers = registry.require(resolver_key, dependency=dependency)

    ctx = registry.require('ctx')

    resolvers = user_resolvers + source_resolvers

    try_resolver = TryResolver(resolvers=resolvers, ctx=ctx)

    return OnActiveStorePathResolver(
        resolver=try_resolver, name=dependency.name,
        sha1=dependency.sha1, active_resolve=active_resolve,
        bundle_config_path=bundle_config_path)


@provide
def dependency_manager(registry):

    ctx = registry.require('ctx')

    registry.provide_value('parser',
        argparse.ArgumentParser(description='Resolve Options',
        # add_help=False will remove the default handling of --help and -h
        # https://docs.python.org/3/library/argparse.html#add-help
        #
        # This will be handled by waf's default options context.
        add_help=False,
        # Remove printing usage help, like:
        #    usage: waf [--bundle-path]
        # When printing help, this seems to be an undocumented feature of
        # argparse: http://stackoverflow.com/a/14591302/1717320
        usage=argparse.SUPPRESS))

    # Dict object which will contain the path to the resolved
    # dependencies.
    cache = dict()
    registry.provide_value('cache', cache)

    return DependencyManager(registry=registry,
        cache=cache, ctx=ctx)

def build_registry(ctx, git_binary, default_bundle_path, bundle_config_path,
    active_resolve, semver, utils, args):
    """ Builds a registry.


    :param ctx: A Waf Context instance.
    :param git_binary: A string containing the path to a git executable.
    :param default_bundle_path: A string containing the path where dependencies
        as default should be downloaded (unless the user overrides).
    :param bundle_config_path: A string containing the path to where the
        dependencies config json files should be / is stored.
    :param active_resolve: Boolean which is True if this is an active resolve
        otherwise False.
    :param semver: The semver module
    :param utils: The waflib.Utils module
    :param args: Argument strings as a list, typically this will come
        from sys.argv

    :returns:
        A new Registery instance.
    """

    registry = Registry()

    registry.provide_value('ctx', ctx)
    registry.provide_value('git_binary', git_binary)
    registry.provide_value('default_bundle_path', default_bundle_path)
    registry.provide_value('bundle_config_path', bundle_config_path)
    registry.provide_value('active_resolve', active_resolve)
    registry.provide_value('semver', semver)
    registry.provide_value('utils', utils)
    registry.provide_value('args', args)

    return registry
