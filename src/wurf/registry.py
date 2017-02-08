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
    # using the @provide decorator
    providers = {}

    # Set which will track which provider functions that produce values
    # that should be cached. This is done using @cache decorator.
    cache_providers = set()

    # Dictionary with functions that should be invoked before a specific
    # provider
    before_provider = defaultdict(set)

    # Dictionary with functions that should be invoked before a specific
    # provider
    after_provider = defaultdict(set)

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

        # Dictionary with functions that should be invoked before a specific
        # provider
        self.before_provider = defaultdict(set)

        # Dictionary with functions that should be invoked before a specific
        # provider
        self.after_provider = defaultdict(set)

        # Set which contains the name of features that should be cached
        if use_cache_providers:
            for s in Registry.cache_providers:
                self.cache_provider(s)

        if use_providers:
            for k,v in Registry.providers.items():
                self.provide(k,v)

    def cache_provider(self, provider_name):
        assert provider_name not in self.cache
        self.cache[provider_name] = {}


    def provide(self, provider_name, provider_function, override=False):
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

            for before in self.before_provider[provider_name]:
                before(registry=self, **kwargs)

            result = provider_function(registry=self, **kwargs)

            for after in self.after_provider[provider_name]:
                after(registry=self, **kwargs)

            return result

        self.registry[provider_name] = call

    def invoke_before(self, provider_name, function):
        assert function not in self.before_provider[provider_name]
        self.before_provider[provider_name].add(function)

    def invoke_after(self, provider_name, function):
        assert function not in self.after_provider[provider_name]
        self.after_provider[provider_name].add(function)

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



@option
def add_user_path(parser, dependency):
    pass

class Option(object):
    def __init__(command, *args):
        pass
        
class DependencyOption(object):
    
    def __init__(self, options, **kwargs):
        self.options = options
        
        self.options.parser.add_
    
    def get(self, options, dependency):
        pass
        
@option
def bundle_path():
    pass
    


class Options(object):
    
    def __init__(self, args, parser, default_bundle_path):
        
        # Using the %default placeholder:
        #    http://stackoverflow.com/a/1254491/1717320
        parser.add_argument('--bundle-path',
            default=default_bundle_path,
            dest='--bundle-path',
            help='The folder where the bundled dependencies are downloaded.'
                 '(default: %(default)s)')
        
        parser.add_argument('--git-protocol',
            dest='--git-protocol',
            help='Use a specific git protocol to download dependencies.'
                 'Supported protocols {}'.format(supported_protocols))
        
    def bundle_path(self):
        return self.options['--bundle-path'] 
        
    def git_protocol(self):
        return self.options['--git-protocol']    
        
    def user_path(self, dependency):
        return self.options['--%s-path' % dependency.name]    

    def use_checkout(self, dependency):
        return self.options['--%s-path' % dependency.name] 
        
    def __add_user_path(self, dependency):
        
        option = '--%s-path' % dependency.name
        
        self.parser.add_argument(option,
        nargs='?',
        dest=option,
        help='Manually specify path for {}.'.format(
        dependency.name))
        
        
    def add_dependency(self, dependency):
        
        
        if dependency.resolver == 'git':
            
            option = '--%s-use-checkout' % dependency.name

            parser.add_argument(option,
                nargs='?',
                dest=option,
                help='Manually specify Git checkout for {}.'.format(
                    dependency.name))



def provide(func):

    if func.__name__ in Registry.providers:
        raise WurfProvideRegistryError(func.__name__)
    Registry.providers[func.__name__] = func

    return func

def invoke_before(func, provider_name):

    assert func not in Registry.before_provider[provider_name]
    Registry.before_provider[provider_name].add(func)

    return func

def invoke_after(func, provider_name):

    assert func not in Registry.after_provider[provider_name]
    Registry.after_provider[provider_name].add(func)

    return func

def cache(func):
    Registry.cache_providers.add(func.__name__)

    return func


@cache
@provide
def git_url_parser(registry):
    """ Parser for Git URLs. """

    return GitUrlParser()

@cache
@provide
def git_url_rewriter(registry):
    """ Rewriter for Git URLs.

    Supports various transformations such as changing/adding the git
    protocol.
    """
    parser = registry.require('git_url_parser')
    git_protocol = registry.require('git_protocol')

    return GitUrlRewriter(parser=parser, rewrite_protocol=git_protocol)

@cache
@provide
def user_git_protocol(registry):
    """ Return the user specified Git protcol.

    If no protocol is specified return None.
    """
    parser = registry.require('parser')
    args = registry.require('args')
    ctx = registry.require('ctx')

    # We support the protocols we know how to rewrite
    supported_protocols = GitUrlRewriter.git_protocols.keys()

    parser.add_argument('--git-protocol',
        help='Use a specific git protocol to download dependencies.'
             'Supported protocols {}'.format(supported_protocols))

    known_args, unknown_args = parser.parse_known_args(args=args)

    protocol = known_args.git_protocol

    if protocol and protocol not in supported:
        ctx.fatal('Unknown git protocol specified: "{}", supported '
                  'protocols are {}'.format(protocol, supported_protocols))

    return protocol

@cache
@provide
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


@cache
@provide
def git(registry):
    """ The Git object, which is used to run git commands.

    :param registry: A Registry instance.
    """
    git_binary = registry.require('git_binary')
    ctx = registry.require('ctx')

    return Git(git_binary=git_binary, ctx=ctx)


@cache
@provide
def git_protocol(registry):
    """ Return the Git protocol to use. """

    # Check if the user specified a git protocol to use:
    protocol = registry.require('user_git_protocol')

    # Check what the parent project uses
    if not protocol:
        protocol = registry.require('project_git_protocol')

    # Finally just use https
    if not protocol:
        protocol = 'https://'

    return protocol


@cache
@provide
def bundle_path(registry):
    """ Provides the path where dependencies should be stored.

    :param registry: A Registry instance
    """
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

    return known_args.bundle_path


@cache
@provide
def user_path(registry, dependency):
    """ Provides the user path to a specific dependency.

    :param registry: A Registry instance
    :param dependency: A Dependency instance.
    """
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
    #registry.provide_value(key, arguments[option])
    # @todo remove
    print(arguments)
    return arguments[option]


@provide
def user_path_resolver(registry, dependency):

    path = registry.require('user_path', dependency=dependency)

    if path:
        return UserPathResolver(path=path)
    else:
        return None


@cache
@provide
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


@provide
def git_resolvers(registry, dependency):
    """ Builds a list of WurfGitResolver instances, one for each source.

    :param registry: A Registry instance.
    :param dependency: A WurfDependency instance.
    """

    git = registry.require('git')
    ctx = registry.require('ctx')
    bundle_path = registry.require('bundle_path')

    name = dependency.name
    sources = registry.require('git_sources', dependency=dependency)

    def new_resolver(source):
        return wurf_git_resolver.GitResolver(
            git=git, ctx=ctx, name=name, bundle_path=bundle_path, source=source)

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
    git_resolvers = registry.require('git_resolvers', dependency=dependency)
    bundle_path = registry.require('bundle_path')

    name = dependency.name
    checkout = dependency.checkout

    def new_resolver(git_resolver):
        return GitCheckoutResolver(git=git, git_resolver=git_resolver, ctx=ctx,
            name=name, bundle_path=bundle_path, checkout=checkout)

    resolvers = [new_resolver(git_resolver) for git_resolver in git_resolvers]
    return resolvers

@provide
def git_semver_resolvers(registry, dependency):
    """ Builds a GitSemverResolver instance.

    :param registry: A Registry instance.
    :param dependency: A WurfDependency instance.
    """

    git = registry.require('git')
    semver = registry.require('semver')
    ctx = registry.require('ctx')
    git_resolvers = registry.require('git_resolvers', dependency=dependency)
    bundle_path = registry.require('bundle_path')

    name = dependency.name
    major = dependency.major

    def new_resolver(git_resolver):
        return GitSemverResolver(git=git, git_resolver=git_resolver, ctx=ctx,
            semver=semver, name=name, bundle_path=bundle_path, major=major)

    resolvers = [new_resolver(git_resolver) for git_resolver in git_resolvers]
    return resolvers


@cache
@provide
def git_user_checkout(registry, dependency):
    """ Provides the user chosen git checkout.

    :param registry: A Registry instance
    :param dependency: A Dependency instance.
    """
    parser = registry.require('parser')
    args = registry.require('args')

    option = '--%s-use-checkout' % dependency.name

    parser.add_argument(option,
        nargs='?',
        dest=option,
        help='Manually specify Git checkout for {}.'.format(dependency.name))

    known_args, unknown_args = parser.parse_known_args(args=args)

    # Access the attribute as a dict:
    # https://docs.python.org/3/library/argparse.html#the-namespace-object
    arguments = vars(known_args)

    return arguments[option]


@cache
@provide
def git_user_checkout_resolver(registry, dependency):
    """ Builds a WurfGitCheckoutResolver instance.

    :param registry: A Registry instance.
    :param dependency: A WurfDependency instance.
    """

    git = registry.require('git')
    ctx = registry.require('ctx')
    git_resolvers = registry.require('git_resolvers', dependency=dependency)
    bundle_path = registry.require('bundle_path')
    checkout = registry.require('git_user_checkout', dependency=dependency)

    if checkout:
        return GitCheckoutResolver(git=git, git_resolver=git_resolver, ctx=ctx,
            name=name, bundle_path=bundle_path, checkout=checkout)
    else:
        return None


@provide
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

@provide
def passive_path_resolver(registry, dependency):
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




@provide
def dependency_resolver(registry, dependency):
    """ Builds a WurfSourceResolver instance."""

    # Collect general options


    active_resolve = registry.require('active_resolve')
    bundle_config_path = registry.require('bundle_config_path')

    user_resolvers = [
        registry.require('user_path_resolver', dependency=dependency),
        registry.require('passive_path_resolver', dependency=dependency)]

    resolver_key = "{}_source_resolvers".format(dependency.resolver)

    source_resolvers = registry.require(resolver_key, dependency=dependency)

    ctx = registry.require('ctx')

    resolvers = user_resolvers + source_resolvers

    print(registry.require('user_path_resolver', dependency=dependency))
    print("wurf: resolvers {}".format(resolvers))

    # Filter out missing resolvers
    resolvers = [r for r in resolvers if r is not None]

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
