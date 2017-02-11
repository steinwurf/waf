#! /usr/bin/env python
# encoding: utf-8

import argparse
import os
from collections import defaultdict

from . import wurf_git_resolver

from . import wurf_user_checkout_resolver
from .user_path_resolver import UserPathResolver
from .dependency_manager import DependencyManager
from .on_active_store_path_resolver import OnActiveStorePathResolver
from .on_passive_load_path_resolver import OnPassiveLoadPathResolver
from .try_resolver import TryResolver
from .git_checkout_resolver import GitCheckoutResolver
from .git_semver_resolver import GitSemverResolver
from .git_url_parser import GitUrlParser
from .git_url_rewriter import GitUrlRewriter
from .git import Git


from . import wurf_error

class WurfProvideRegistryError(wurf_error.WurfError):
    """Generic exception for wurf"""
    def __init__(self, name):

        self.name = name

        super(WurfProvideRegistryError, self).__init__(
            "Fatal error {} alredy added to registry".format(self.name))

class Registry(object):

    # Dictionary containing the provider functions registered
    # using the @Registry.provide decorator
    providers = {}

    # Set which will track which provider functions that produce values
    # that should be cached. This is done using @Registry.cache decorator.
    cache_providers = set()

    def __init__(self, use_providers=True, use_cache_providers=True):
        """
        :param use_providers: True if the class providers should be added. False
            will create a new Registry instance without any added providers.
        """

        # Dictionary which will contain the feature as a key and a
        # provider function as value
        self.registry = {}

        # Dictionary which contains cached values produced for the different
        # providers. The layout of the dictionary will be:
        # { 'provider1': { argument_hash1: value1
        #                  arguemnt_hash2, value2},
        #   'provider2': { argument_hash1: value1 },
        #   ....
        # }
        #
        # Where the provider name is the key to a dictionary where cached values
        # are stored. The nested dict uses a hash of the arguments passed to
        # require(...) to find the right cached response.
        self.cache = {}

        # Set which contains the name of features that should be cached
        if use_cache_providers:
            for s in Registry.cache_providers:
                self.cache_provider(s)

        if use_providers:
            for k,v in Registry.providers.items():
                self.provide_function(k,v)

    def cache_provider(self, provider_name):
        assert provider_name not in self.cache
        self.cache[provider_name] = {}

    def purge_cache(self):
        for provider_name in self.cache:
            self.cache[provider_name] = {}

    def provide_function(self, provider_name, provider_function, override=False):
        """
        :param provider_name: The name of the provider as a string
        :param provider_function: Function to call which will provide the value
        :param cache: Determines whether calls to the provider should be cached.
            If arguments are passed to the provider in the require(...)
            function, they must be hashable.
        :param override: Determines whether the provider should override/replace
            an existing provider. If True we will override an existing provider
            with the same name.
        """

        if not override and provider_name in self.registry:
            raise WurfProvideRegistryError(provider_name)

        def call(**kwargs):
            return provider_function(registry=self, **kwargs)

        self.registry[provider_name] = call
        
        if provider_name in self.cache:
            # Clean the cache
            self.cache[provider_name] = {}


    def provide_value(self, provider_name, value):
        """
        :param provider_name: The name of the provider as a string
        :param value: The value with should be returned on require(...)
        """

        # @todo add override parameter / check

        def call(): return value
        self.registry[provider_name] = call


    def require(self, provider_name, **kwargs):
        """
        :param provider_name: The name of the provider as a string
        :param kwargs: Keyword arguments that should be passed to the provider
            function.
        """

        if provider_name in self.cache:
            # Did we already cache?
            key = frozenset(kwargs.items())

            try:
                return self.cache[provider_name][key]
            except KeyError:
                call = self.registry[provider_name]
                result = call(**kwargs)
                self.cache[provider_name][key] = result
                return result
        else:
            call = self.registry[provider_name]
            result = call(**kwargs)
            return result

    def __contains__(self, provider_name):
        """
        :param provider_name: The name of the provider as a string
        :return: True if the provider is in the registry
        """
        return provider_name in self.registry

    @staticmethod
    def cache(func):
        Registry.cache_providers.add(func.__name__)

        return func
        
    @staticmethod
    def provide(func):

        if func.__name__ in Registry.providers:
            raise WurfProvideRegistryError(func.__name__)
        Registry.providers[func.__name__] = func

        return func



class Options(object):
    
    def __init__(self, args, parser, default_bundle_path, 
        supported_git_protocols):
        
        self.args = args
        self.parser = parser
        
        self.known_args = {}
        self.unknown_args = []
        
        # Using the %default placeholder:
        #    http://stackoverflow.com/a/1254491/1717320
        self.parser.add_argument('--bundle-path',
            default=default_bundle_path,
            dest='--bundle-path',
            help='The folder where the bundled dependencies are downloaded.'
                 '(default: %(default)s)')
        
        self.parser.add_argument('--git-protocol',
            dest='--git-protocol',
            help='Use a specific git protocol to download dependencies.'
                 'Supported protocols {}'.format(supported_git_protocols))
        
        self.__parse()
        
    def bundle_path(self):
        return self.known_args['--bundle-path'] 
        
    def git_protocol(self):
        return self.known_args['--git-protocol']    
        
    def path(self, dependency):
        return self.known_args['--%s-path' % dependency.name]    

    def use_checkout(self, dependency):
        return self.known_args['--%s-use-checkout' % dependency.name] 
        
    def __parse(self):
        
        known, unknown = self.parser.parse_known_args(args=self.args)
        
        self.known_args = vars(known)
        self.unknown_args = unknown    
    
    def __add_path(self, dependency):
        
        option = '--%s-path' % dependency.name
        
        self.parser.add_argument(option,
            nargs='?',
            dest=option,
            help='Manually specify path for {}.'.format(
                dependency.name))
        
    def __add_use_checkout(self, dependency):
        
        option = '--%s-use-checkout' % dependency.name

        self.parser.add_argument(option,
            nargs='?',
            dest=option,
            help='Manually specify Git checkout for {}.'.format(
                dependency.name))

    def add_dependency(self, dependency):
        
        self.__add_path(dependency)
        
        if dependency.resolver == 'git':
            
            self.__add_use_checkout(dependency)

        self.__parse()






@Registry.cache
@Registry.provide
def git_url_parser(registry):
    """ Parser for Git URLs. """

    return GitUrlParser()

@Registry.cache
@Registry.provide
def git_url_rewriter(registry):
    """ Rewriter for Git URLs.

    Supports various transformations such as changing/adding the git
    protocol.
    """
    parser = registry.require('git_url_parser')
    git_protocol = registry.require('git_protocol')

    return GitUrlRewriter(parser=parser, rewrite_protocol=git_protocol)

@Registry.cache
@Registry.provide
def parser(registry):
    return argparse.ArgumentParser(description='Resolve Options',
        # add_help=False will remove the default handling of --help and -h
        # https://docs.python.org/3/library/argparse.html#add-help
        #
        # This will be handled by waf's default options context.
        add_help=False,
        # Remove printing usage help, like:
        #    usage: waf [--bundle-path]
        # When printing help, this seems to be an undocumented feature of
        # argparse: http://stackoverflow.com/a/14591302/1717320
        usage=argparse.SUPPRESS)

@Registry.cache
@Registry.provide
def cache(registry):
    return dict()

@Registry.cache
@Registry.provide
def options(registry):
    """ Return the Options provider.

    """
    parser = registry.require('parser')
    args = registry.require('args')
    default_bundle_path = registry.require('default_bundle_path')
    
    # We support the protocols we know how to rewrite
    supported_git_protocols = GitUrlRewriter.git_protocols.keys()

    return Options(args=args, parser=parser, 
        default_bundle_path=default_bundle_path, 
        supported_git_protocols=supported_git_protocols)
    
    

@Registry.cache
@Registry.provide
def project_git_protocol(registry):
    """ Return the Git protocol used by the parent project.

    If parent project not under git version control return None.
    """
    git = registry.require('git')
    ctx = registry.require('ctx')
    parser = registry.require('git_url_parser')

    try:
        parent_url = git.remote_origin_url(cwd=os.getcwd())

    except Exception as e:

        ctx.to_log('Exception when executing git.remote_origin_url {}'.format(e))
        return None

    else:

        url = parser.parse(parent_url)
        return url.protocol


@Registry.cache
@Registry.provide
def git(registry):
    """ The Git object, which is used to run git commands.

    :param registry: A Registry instance.
    """
    git_binary = registry.require('git_binary')
    ctx = registry.require('ctx')

    return Git(git_binary=git_binary, ctx=ctx)


@Registry.cache
@Registry.provide
def git_protocol(registry):
    """ Return the Git protocol to use. """

    options = registry.require('options')

    # Check if the user specified a git protocol to use:
    protocol = options.git_protocol()

    # Check what the parent project uses
    if not protocol:
        protocol = registry.require('project_git_protocol')

    # Finally just use https
    if not protocol:
        protocol = 'https://'

    return protocol



@Registry.provide
def user_path_resolver(registry, dependency):

    options = registry.require('options')

    path = options.path(dependency=dependency)

    if path:
        return UserPathResolver(path=path)
    else:
        return None


@Registry.cache
@Registry.provide
def git_sources(registry, dependency):
    """ Takes the dependency sources and re-writes the with the desired
    git protocol.

    If needed this is also the place where "addition" sources could be added.
    E.g. one could add additional mirrors or alternative protocols to try.

    :param registry: A Registry instance.
    :param dependency: A WurfDependency instance.
    """
    rewriter = registry.require('git_url_rewriter')

    sources = [rewriter.rewrite_url(s) for s in dependency.sources]

    return sources


@Registry.provide
def git_resolvers(registry, dependency):
    """ Builds a list of WurfGitResolver instances, one for each source.

    :param registry: A Registry instance.
    :param dependency: A WurfDependency instance.
    """

    git = registry.require('git')
    ctx = registry.require('ctx')
    options = registry.require('options')
    
    bundle_path = options.bundle_path()
    name = dependency.name
    sources = registry.require('git_sources', dependency=dependency)

    def new_resolver(source):
        return wurf_git_resolver.GitResolver(
            git=git, ctx=ctx, name=name, bundle_path=bundle_path, source=source)

    resolvers = [new_resolver(source) for source in sources]
    return resolvers


@Registry.provide
def git_checkout_resolvers(registry, dependency):
    """ Builds a WurfGitCheckoutResolver instance.

    :param registry: A Registry instance.
    :param dependency: A WurfDependency instance.
    """

    git = registry.require('git')
    ctx = registry.require('ctx')    
    options = registry.require('options')

    git_resolvers = registry.require('git_resolvers', dependency=dependency)
    
    bundle_path = options.bundle_path()
    name = dependency.name
    checkout = dependency.checkout

    def new_resolver(git_resolver):
        return GitCheckoutResolver(git=git, git_resolver=git_resolver, ctx=ctx,
            name=name, bundle_path=bundle_path, checkout=checkout)

    resolvers = [new_resolver(git_resolver) for git_resolver in git_resolvers]
    return resolvers

@Registry.provide
def git_semver_resolvers(registry, dependency):
    """ Builds a GitSemverResolver instance.

    :param registry: A Registry instance.
    :param dependency: A WurfDependency instance.
    """

    git = registry.require('git')
    semver = registry.require('semver')
    ctx = registry.require('ctx')
    git_resolvers = registry.require('git_resolvers', dependency=dependency)
    options = registry.require('options')
    
    bundle_path = options.bundle_path()
    name = dependency.name
    major = dependency.major

    def new_resolver(git_resolver):
        return GitSemverResolver(git=git, git_resolver=git_resolver, ctx=ctx,
            semver=semver, name=name, bundle_path=bundle_path, major=major)

    resolvers = [new_resolver(git_resolver) for git_resolver in git_resolvers]
    return resolvers



@Registry.cache
@Registry.provide
def git_user_checkout_resolver(registry, dependency):
    """ Builds a WurfGitCheckoutResolver instance.

    :param registry: A Registry instance.
    :param dependency: A WurfDependency instance.
    """

    git = registry.require('git')
    ctx = registry.require('ctx')
    git_resolvers = registry.require('git_resolvers', dependency=dependency)
    options = registry.require('options')
    
    bundle_path = options.bundle_path()
    checkout = options.use_checkout(dependency=dependency)

    if checkout:
        return GitCheckoutResolver(git=git, git_resolver=git_resolver, ctx=ctx,
            name=name, bundle_path=bundle_path, checkout=checkout)
    else:
        return None


@Registry.provide
def git_source_resolvers(registry, dependency):
    """ Builds git resolvers

    :param registry: A Registry instance.
    :param dependency: A WurfDependency instance.
    """

    method = dependency.method
    method_key = "git_{}_resolvers".format(method)

    user_resolvers = [
        registry.require('git_user_checkout_resolver', dependency=dependency)]

    source_resolvers = registry.require(method_key, dependency=dependency)

    resolvers = user_resolvers + source_resolvers

    return resolvers

@Registry.provide
def on_passive_load_path_resolver(registry, dependency):
    """ Builds a WurfPassivePathResolver instance.

    :param registry: A Registry instance.
    """

    ctx = registry.require('ctx')
    bundle_config_path = registry.require('bundle_config_path')
    active_resolve = registry.require('active_resolve')

    if active_resolve:
        return None

    name = dependency.name
    sha1 = dependency.sha1

    return OnPassiveLoadPathResolver(ctx=ctx, name=name, sha1=sha1,
        bundle_config_path=bundle_config_path)


@Registry.provide
def passive_dependency_resolver(registry, dependency):
    
    ctx = registry.require('ctx')
    
    resolvers = [
        registry.require('on_passive_load_path_resolver', dependency=dependency)]

    try_resolver = TryResolver(resolvers=resolvers, ctx=ctx)

    context_msg_resolver = ContextMsgResolver(resolver=try_resolver, 
        ctx=ctx, dependency=dependency)
        
    optional_resolver = OptionalResolver(resolver=context_msg_resolver,
        dependency=dependency)
    
    return try_resolver
        
@Registry.provide
def active_dependency_resolver(registry, dependency):
    
    bundle_config_path = registry.require('bundle_config_path')

    user_resolvers = [
        registry.require('user_path_resolver', dependency=dependency)]

    resolver_key = "{}_source_resolvers".format(dependency.resolver)

    source_resolvers = registry.require(resolver_key, dependency=dependency)

    resolvers = user_resolvers + source_resolvers

    try_resolver = TryResolver(resolvers=resolvers, ctx=ctx)
    
    context_msg_resolver = ContextMsgResolver(resolver=try_resolver, 
        ctx=ctx, dependency=dependency)

    optional_resolver = OptionalResolver(resolver=context_msg_resolver,
        dependency=dependency)

    return OnActiveStorePathResolver(
        resolver=optional_resolver, name=dependency.name,
        sha1=dependency.sha1, bundle_config_path=bundle_config_path)
    

@Registry.provide
def dependency_resolver(registry, dependency):
    """ Builds a WurfSourceResolver instance."""

    # This is where we "wire" together the resolvers. Which actually do the
    # work of via some method obtaining a path to a dependency.
    # 
    # There are three resolver chains/configurations:
    # 
    # 1. The "active" chain: This chain goes to the network and fetches stuff
    # 2. The "passive" chain: This chain will load information from the 
    #    file system. 
    # 3. The "help" chain: This chain tries to interate though as many 
    #    dependencies as possible to get all options.

    active_resolve = registry.require('active_resolve')



@Registry.provide
def dependency_manager(registry):
    
    # Clean the cache such that we get "fresh" objects
    registry.purge_cache()

    ctx = registry.require('ctx')
    cache = registry.require('cache')
    options = registry.require('options')

    return DependencyManager(registry=registry,
        cache=cache, ctx=ctx, options=options)


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
