#! /usr/bin/env python
# encoding: utf-8

import argparse

from . import wurf_git
from . import wurf_git_url_resolver
from . import wurf_git_resolver
from . import wurf_git_checkout_resolver
from . import wurf_git_semver_resolver
from . import wurf_source_resolver
from . import wurf_user_checkout_resolver
from . import wurf_user_path_resolver
from . import wurf_hash_manager

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

    def provide(self, feature, provider, **kwargs):

        def call(**_kwargs):

            # Python 2.x does not allow two keyword dicts, so we merge
            # them manually:
            # http://stackoverflow.com/a/33350709/1717320
            for k, v in _kwargs.items():
                if k in kwargs:
                    raise RuntimeError('No duplicates')
                kwargs[k] = v

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


def build_wurf_git_resolver(registry):
    """ Builds a WurfGitResolver instance."""

    git = registry.require('git')
    url_resolver = registry.require('git_url_resolver')
    ctx = registry.require('ctx')

    return wurf_git_resolver.WurfGitResolver(
        git=git, url_resolver=url_resolver, ctx=ctx)

def build_wurf_git_checkout_resolver(registry):
    """ Builds a WurfGitResolver instance."""

    git = registry.require('git')
    git_resolver = registry.require('git_resolver')
    ctx = registry.require('ctx')

    return wurf_git_checkout_resolver.WurfGitCheckoutResolver(
        git=git, git_resolver=git_resolver, ctx=ctx)

def build_wurf_git_semver_resolver(registry):
    """ Builds a WurfGitSemverResolver instance."""

    git = registry.require('git')
    git_resolver = registry.require('git_resolver')
    ctx = registry.require('ctx')
    semver = registry.require('semver')

    return wurf_git_semver_resolver.WurfGitSemverResolver(
        git=git, git_resolver=git_resolver, ctx=ctx, semver=semver)

def build_wurf_git_method_resolver(registry):
    """ Builds a WurfGitMethodResolver instance."""

    user_methods = [registry.require('user_checkout_resolver')]

    git_methods = {
        'checkout': registry.require('git_checkout_resolver'),
        'semver': registry.require('git_semver_resolver')}

    return wurf_source_resolver.WurfGitMethodResolver(
        user_methods=user_methods, git_methods=git_methods)

def build_wurf_user_checkout_resolver(registry):
    """ Builds a WurfUserCheckoutResolver instance."""

    git_checkout_resolver = registry.require('git_checkout_resolver')
    parser = registry.require('parser')

    return wurf_user_checkout_resolver.WurfUserCheckoutResolver(
        parser=parser, git_checkout_resolver=git_checkout_resolver)

def build_wurf_user_path_resolver(registry):
    """ Builds a WurfUserPathResolver instance."""

    parser = registry.require('parser')
    args = registry.require('args')

    return wurf_user_path_resolver.WurfUserPathResolver(
        parser=parser, args=args)

def build_source_resolver(registry):
    """ Builds a WurfSourceResolver instance."""

    user_resolvers = [registry.require('user_path_resolver')]

    type_resolvers = {
        'git': registry.require('git_method_resolver')}

    ctx = registry.require('ctx')

    return wurf_source_resolver.WurfSourceResolver(
        user_resolvers=user_resolvers, type_resolvers=type_resolvers, ctx=ctx)

def build_wurf_git(registry):
    """ Builds a WurfGit instance."""

    ctx = registry.require('ctx')
    git_binary = registry.require('git_binary')

    return wurf_git.WurfGit(git_binary=git_binary, ctx=ctx)

def build_git_url_resolver(registry):

    return wurf_git_url_resolver.WurfGitUrlResolver()

def build_hash_manager(registry):
    return wurf_hash_manager.WurfHashManager()

def build_skip_seen_dependency_resolver(registry):
    ctx = registry.require('ctx')
    return wurf_source_resolver.WurfSkipSeenDependency(ctx=ctx)

def build_bundle_path_resolver(registry):
    utils = registry.require('utils')
    parser = registry.require('parser')
    default_bundle_path = registry.require('default_bundle_path')
    args = registry.require('args')

    return wurf_source_resolver.WurfBundlePath(utils=utils,
        parser=parser, default_bundle_path=default_bundle_path, args=args)

def build_active_dependency_resolver(registry):
    ctx = registry.require('ctx')

    return wurf_source_resolver.WurfActiveDependencyResolver(ctx=ctx,
        registry=registry)

def build_passive_dependency_resolver(registry):
    ctx = registry.require('ctx')
    bundle_config_path = registry.require('bundle_config_path')

    return wurf_source_resolver.WurfPassiveDependencyResolver(
        ctx=ctx, bundle_config_path=bundle_config_path)

def build_store_dependency_resolver(registry):
    bundle_config_path = registry.require('bundle_config_path')

    return wurf_source_resolver.WurfStoreDependency(
        bundle_config_path=bundle_config_path)

def build_recurse_dependency_resolver(registry):
    ctx = registry.require('ctx')

    return wurf_source_resolver.WurfRecurseDependency(ctx=ctx)

def build_cache_dependency_resolver(registry):
    cache = registry.require('cache')

    return wurf_source_resolver.WurfCacheDependency(cache=cache)

def build_null_dependency_resolver(registry):

    return wurf_source_resolver.WurfNullResolver()

def build_dependency_manager(registry):

    # The dependency manager instance modifies state of the following
    # objects these therefore should be unique for each manager built

    active_resolve = registry.require('active_resolve')

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
    registry.provide_value('cache', {})

    if active_resolve:
        return build_active_dependency_manager(registry)
    else:
        return build_passive_dependency_manager(registry)

def build_active_dependency_manager(registry):

    hash_manager = registry.require('hash_manager')
    skip_resolver = registry.require('skip_seen_dependency_resolver')
    active_resolver = registry.require('active_dependency_resolver')
    store_resolver = registry.require('store_dependency_resolver')
    recurse_resolver = registry.require('recurse_dependency_resolver')
    cache_resolver = registry.require('cache_dependency_resolver')
    null_resolver = registry.require('null_dependency_resolver')

    hash_manager.next_resolver = skip_resolver
    skip_resolver.next_resolver = active_resolver
    #bundle_path_resolver.next_resolver = active_resolver
    active_resolver.next_resolver = store_resolver
    store_resolver.next_resolver = recurse_resolver
    recurse_resolver.next_resolver = cache_resolver
    cache_resolver.next_resolver = null_resolver

    return hash_manager

def build_passive_dependency_manager(registry):

    hash_manager = registry.require('hash_manager')
    skip_resolver = registry.require('skip_seen_dependency_resolver')
    active_resolver = registry.require('active_dependency_resolver')
    recurse_resolver = registry.require('recurse_dependency_resolver')
    cache_resolver = registry.require('cache_dependency_resolver')
    null_resolver = registry.require('null_dependency_resolver')

    hash_manager.next_resolver = skip_resolver
    skip_resolver.next_resolver = active_resolver
    active_resolver.next_resolver = recurse_resolver
    recurse_resolver.next_resolver = cache_resolver
    cache_resolver.next_resolver = null_resolver

    return hash_manager



############################################################
############################################################
############################################################
############################################################

@provide
def bundle_path(registry):
    """ Provides the user path to a specific dependency.

    :param registry: A Registry instance
    :param name: The name of a dependency as a string
    """

    key = 'parsed_bundle_path'

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
def git_method_source_resolvers(registry, dependency):
    """ Builds a WurfGitMethodResolver instance.

    :param registry: A Registry instance
    :param dependency: A WurfDependency instance.
    """

    method = dependency.method
    method_key = "git_{}_source_resolvers".format(method)

    return registry.require(method_key, dependency=dependency)


@provide
def user_path(registry, dependency):
    """ Provides the user path to a specific dependency.

    :param registry: A Registry instance
    :param dependency: A WurfDependency instance.
    """

    key = 'parsed_{}_user_path'.format(dependency.name)

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
def user_path_resolver2(registry, dependency):

    path = registry.require('user_path', dependency=dependency)

    return wurf_user_path_resolver.WurfUserPathResolver2(path=path)

@provide
def git_source_resolvers(registry, dependency):
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
        return wurf_git_resolver.WurfGitResolver2(
            git=git, url_resolver=url_resolver, ctx=ctx, name=name,
            bundle_path=bundle_path, source=source)

    resolvers = [new_resolver(source) for source in sources]
    return resolvers

@provide
def passive_path_resolver(registry, dependency):
    """ Builds a WurfPassivePathResolver instance.

    :param registry: A Registry instance.
    :param dependency: A WurfDependency instance.
    """

    ctx = registry.require('ctx')
    bundle_config_path = registry.require('bundle_config_path')
    active_resolve = registry.require('active_resolve')

    name = dependency.name
    sha1 = dependency.sha1

    return wurf_source_resolver.WurfPassivePathResolver(ctx=ctx, name=name,
        sha1=sha1, active_resolve=active_resolve, bundle_config_path=bundle_config_path)

@provide
def git_checkout_source_resolvers(registry, dependency):
    """ Builds a WurfGitCheckoutResolver instance.

    :param registry: A Registry instance.
    :param dependency: A WurfDependency instance.
    """

    git = registry.require('git')
    ctx = registry.require('ctx')
    git_resolvers = registry.require('git_method_source_resolvers',
        dependency=dependency)
    bundle_path = registry.require('bundle_path')

    name = dependency.name
    checkout = dependency.checkout

    def new_resolver(git_resolver):
        return wurf_git_checkout_resolver.WurfGitCheckoutResolver2(
            git=git, git_resolver=git_resolver, ctx=ctx, name=name,
            bundle_path=bundle_path, checkout=checkout)

    resolvers = [new_resolver(git_resolver) for git_resolver in git_resolvers]
    return resolvers

def build_wurf_git_semver_resolver2(registry, dependency):
    """ Builds a WurfGitCheckoutResolver instance.

    :param registry: A Registry instance.
    :param dependency: A WurfDependency instance.
    """

    git = registry.require('git')
    ctx = registry.require('ctx')
    semver = registry.require('semver')
    git_resolvers = registry.require('git_resolver', dependency=dependency)
    bundle_path = registry.require('bundle_path')

    name = dependency.name
    major = dependency.major

    def new_resolver(git_resolver):
        return wurf_git_checkout_resolver.WurfGitSemverResolver2(
            git=git, git_resolver=git_resolver, ctx=ctx, semver=semver,
            name=name, bundle_path=bundle_path, major=major)

    resolvers = [new_resolver(git_resolver) for git_resolver in git_resolvers]
    return resolvers

@provide
def dependency_resolver2(registry, dependency):
    """ Builds a WurfSourceResolver instance."""

    active_resolve = registry.require('active_resolve')
    bundle_config_path = registry.require('bundle_config_path')

    user_resolvers = [
        registry.require('user_path_resolver2', dependency=dependency),
        registry.require('passive_path_resolver', dependency=dependency)]

    resolver_key = "{}_source_resolvers".format(dependency.resolver)

    source_resolvers = registry.require(resolver_key, dependency=dependency)

    ctx = registry.require('ctx')

    resolvers = user_resolvers + source_resolvers

    source_resolver = wurf_source_resolver.WurfSourceResolver2(
        name=dependency.name, resolvers=resolvers, ctx=ctx)

    return wurf_source_resolver.WurfOnActiveStorePathResolver(
        resolver=source_resolver, name=dependency.name,
        sha1=dependency.sha1, active_resolve=active_resolve,
        bundle_config_path=bundle_config_path)



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

    registry.provide('git', build_wurf_git)
    registry.provide('git_url_resolver', build_git_url_resolver)
    registry.provide('git_resolver', build_wurf_git_resolver)
    registry.provide('git_checkout_resolver', build_wurf_git_checkout_resolver)
    registry.provide('git_semver_resolver', build_wurf_git_semver_resolver)
    registry.provide('user_checkout_resolver', build_wurf_user_checkout_resolver)
    registry.provide('user_path_resolver', build_wurf_user_path_resolver)
    registry.provide('git_method_resolver', build_wurf_git_method_resolver)
    registry.provide('source_resolver', build_source_resolver)
    registry.provide('hash_manager', build_hash_manager)
    registry.provide('skip_seen_dependency_resolver',
        build_skip_seen_dependency_resolver)
    registry.provide('bundle_path_resolver', build_bundle_path_resolver)
    registry.provide('active_dependency_resolver',
        build_active_dependency_resolver)
    registry.provide('store_dependency_resolver', build_store_dependency_resolver)
    registry.provide('recurse_dependency_resolver', build_recurse_dependency_resolver)
    registry.provide('cache_dependency_resolver', build_cache_dependency_resolver)
    registry.provide('null_dependency_resolver', build_null_dependency_resolver)
    registry.provide('passive_dependency_resolver', build_passive_dependency_resolver)
    registry.provide('dependency_manager', build_dependency_manager)

    return registry
