#! /usr/bin/env python
# encoding: utf-8

import argparse
import os
import json
from collections import OrderedDict

from .git_resolver import GitResolver
from .path_resolver import PathResolver
from .context_msg_resolver import ContextMsgResolver
from .dependency_manager import DependencyManager
from .check_optional_resolver import CheckOptionalResolver
from .on_active_store_path_resolver import OnActiveStorePathResolver
from .on_passive_load_path_resolver import OnPassiveLoadPathResolver
from .try_resolver import TryResolver
from .list_resolver import ListResolver
from .git_checkout_resolver import GitCheckoutResolver
from .git_semver_resolver import GitSemverResolver
from .git_url_parser import GitUrlParser
from .git_url_rewriter import GitUrlRewriter
from .git import Git
from .options import Options
from .mandatory_options import MandatoryOptions
from .create_symlink_resolver import CreateSymlinkResolver
from .configuration import Configuration
from .store_lock_path_resolver import StoreLockPathResolver
from .load_lock_path_resolver import LoadLockPathResolver
from .store_lock_version_resolver import StoreLockVersionResolver
from .check_lock_cache_resolver import CheckLockCacheResolver
from .lock_cache import LockCache
from .semver_selector import SemverSelector
from .tag_database import TagDatabase
from .existing_tag_resolver import ExistingTagResolver
from .parent_folder import ParentFolder

from .error import Error
from .error import DependencyError


class WurfProvideRegistryError(Error):
    """Generic exception for wurf"""
    def __init__(self, name):

        self.name = name

        super(WurfProvideRegistryError, self).__init__(
            "Fatal error {} already added to registry".format(self.name))


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


@Registry.cache
@Registry.provide
def resolve_path(registry):
    mandatory_options = registry.require('mandatory_options')
    resolve_path = mandatory_options.resolve_path()
    resolve_path = os.path.abspath(os.path.expanduser(resolve_path))

    waf_utils = registry.require('waf_utils')
    waf_utils.check_dir(resolve_path)

    return resolve_path


@Registry.cache
@Registry.provide
def symlinks_path(registry):
    mandatory_options = registry.require('mandatory_options')
    symlinks_path = mandatory_options.symlinks_path()
    symlinks_path = os.path.abspath(os.path.expanduser(symlinks_path))

    waf_utils = registry.require('waf_utils')
    waf_utils.check_dir(symlinks_path)

    return symlinks_path


@Registry.cache
@Registry.provide
def parent_folder(registry):
    resolve_path = registry.require('resolve_path')

    return ParentFolder(resolve_path=resolve_path)


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
        # This will be handled by waf's default options context.
        add_help=False)


@Registry.cache
@Registry.provide
def dependency_cache(registry):
    return OrderedDict()


@Registry.cache
@Registry.provide
def lock_cache(registry):

    configuration = registry.require('configuration')

    if configuration.resolver_chain() == Configuration.RESOLVE_AND_LOCK:
        options = registry.require('options')
        return LockCache.create_empty(options=options)
    elif configuration.resolver_chain() == Configuration.RESOLVE_FROM_LOCK:
        project_path = registry.require('project_path')
        lock_path = os.path.join(project_path, Configuration.LOCK_FILE)
        return LockCache.create_from_file(lock_path=lock_path)
    else:
        raise Error("Lock cache not available for {} chain".format(
            configuration.resolver_chain()))

@Registry.cache
@Registry.provide
def options(registry):
    """ Return the Options provider.

    """
    parser = registry.require('parser')
    args = registry.require('args')
    default_resolve_path = registry.require('default_resolve_path')
    default_symlinks_path = registry.require('default_symlinks_path')

    # We support the protocols we know how to rewrite
    supported_git_protocols = GitUrlRewriter.git_protocols.keys()

    return Options(args=args, parser=parser,
        default_resolve_path=default_resolve_path,
        default_symlinks_path=default_symlinks_path,
        supported_git_protocols=supported_git_protocols)


@Registry.cache
@Registry.provide
def mandatory_options(registry):
    """ Return the Options provider. """
    options = registry.require('options')

    return MandatoryOptions(options=options)


@Registry.cache
@Registry.provide
def semver_selector(registry):
    """ Return the SemverSelector provider. """
    semver = registry.require('semver')

    return SemverSelector(semver=semver)


@Registry.cache
@Registry.provide
def tag_database(registry):
    """ Return the TagDatabase provider. """
    ctx = registry.require('ctx')
    return TagDatabase(ctx=ctx)


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
        ctx.to_log(
            'Exception when executing git.remote_origin_url: {}'.format(e))
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

    mandatory_options = registry.require('mandatory_options')
    path = mandatory_options.path(dependency=dependency)

    ctx = registry.require('ctx')

    # Set the resolver method on the dependency
    dependency.resolver_action = 'user path'

    resolver = PathResolver(dependency=dependency, path=path)

    return resolver


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
    parent_folder = registry.require('parent_folder')

    name = dependency.name
    sources = registry.require('git_sources', dependency=dependency)

    def wrap(source):
        return GitResolver(git=git, ctx=ctx, parent_folder=parent_folder,
                           name=name, source=source)

    resolvers = [wrap(source) for source in sources]
    return resolvers


@Registry.provide
def git_checkout_list_resolver(registry, dependency, checkout):
    """ Builds a WurfGitCheckoutResolver instance.

    :param registry: A Registry instance.
    :param dependency: A Dependency instance.
    :param checkout: The checkout to use.
    """

    git = registry.require('git')
    ctx = registry.require('ctx')
    options = registry.require('options')

    git_resolvers = registry.require('git_resolvers', dependency=dependency)

    def wrap(resolver):

        resolver = GitCheckoutResolver(git=git, git_resolver=resolver, ctx=ctx,
            dependency=dependency, checkout=checkout)

        resolver = TryResolver(resolver=resolver, ctx=ctx)
        return resolver

    resolvers = [wrap(git_resolver) for git_resolver in git_resolvers]

    resolver = ListResolver(resolvers=resolvers)

    return resolver


@Registry.provide
def resolve_git_checkout(registry, dependency):
    """ Builds a WurfGitCheckoutResolver instance.

    :param registry: A Registry instance.
    :param dependency: A Dependency instance.
    :param checkout: The checkout to use. If None we use the checkout
        specified in the Dependency.
    """
    ctx = registry.require('ctx')

    # Set the resolver method on the dependency
    dependency.resolver_action = 'git checkout'

    resolver = registry.require('git_checkout_list_resolver',
        dependency=dependency, checkout=dependency.checkout)

    resolver = CheckOptionalResolver(resolver=resolver, dependency=dependency)

    return resolver


@Registry.provide
def resolve_git_semver(registry, dependency):
    """ Builds a GitSemverResolver instance.

    :param registry: A Registry instance.
    :param dependency: A WurfDependency instance.
    """

    git = registry.require('git')
    semver_selector = registry.require('semver_selector')
    ctx = registry.require('ctx')
    git_resolvers = registry.require('git_resolvers', dependency=dependency)
    options = registry.require('options')

    # Set the resolver method on the dependency
    dependency.resolver_action = 'git semver'

    def wrap(resolver):
        resolver = GitSemverResolver(git=git, git_resolver=resolver, ctx=ctx,
            semver_selector=semver_selector, dependency=dependency)

        resolver = TryResolver(resolver=resolver, ctx=ctx)
        return resolver

    resolvers = [wrap(git_resolver) for git_resolver in git_resolvers]

    resolver = ListResolver(resolvers=resolvers)
    resolver = CheckOptionalResolver(resolver=resolver, dependency=dependency)

    return resolver


@Registry.cache
@Registry.provide
def resolve_git_user_checkout(registry, dependency):
    """ Builds resolver that uses a user specified checkout.

    :param registry: A Registry instance.
    :param dependency: A Dependency instance.
    """
    ctx = registry.require('ctx')

    mandatory_options = registry.require('mandatory_options')
    checkout = mandatory_options.checkout(dependency=dependency)

    # Set the resolver method on the dependency
    dependency.resolver_action = 'git user checkout'

    # When the user specified the checkout one must succeed:
    resolver = registry.require('git_checkout_list_resolver',
        dependency=dependency, checkout=checkout)

    resolver = MandatoryResolver(resolver=resolver,
        msg="User checkout of {} failed.".format(checkout),
        dependency=dependency)

    return resolver


@Registry.provide
def resolve_git(registry, dependency):
    """ Builds git resolvers

    :param registry: A Registry instance.
    :param dependency: A WurfDependency instance.
    """
    ctx = registry.require('ctx')
    options = registry.require('options')
    checkout = options.checkout(dependency=dependency)

    # If the user specified a checkout we should use that
    if checkout:
        return registry.require('resolve_git_user_checkout',
            dependency=dependency)

    method_key = "resolve_git_{}".format(dependency.method)
    git_resolver = registry.require(method_key, dependency=dependency)

    if options.fast_resolve():

        # Set the resolver action on the dependency
        dependency.resolver_action = 'fast/'+dependency.resolver_action

        resolve_config_path = registry.require('resolve_config_path')

        fast_resolver = OnPassiveLoadPathResolver(dependency=dependency,
            resolve_config_path=resolve_config_path)

        fast_resolver = TryResolver(resolver=fast_resolver, ctx=ctx)

        return ListResolver(resolvers=[fast_resolver, git_resolver])

    elif dependency.method == 'semver':

        sources = registry.require('git_sources', dependency=dependency)
        semver_selector = registry.require('semver_selector')
        tag_database = registry.require('tag_database')
        parent_folder = registry.require('parent_folder')

        existing_tag_resolver = ExistingTagResolver(ctx=ctx,
            dependency=dependency, semver_selector=semver_selector,
            tag_database=tag_database, parent_folder=parent_folder,
            sources=sources)

        return ListResolver(resolvers=[existing_tag_resolver, git_resolver])

    else:

        return git_resolver


@Registry.cache
@Registry.provide
def resolve_from_lock_git(registry, dependency):
    """ Builds resolver that uses a specific checkout provided by the lock file.

    :param registry: A Registry instance.
    :param dependency: A Dependency instance.
    """

    lock_cache = registry.require('lock_cache')
    checkout = lock_cache.checkout(dependency=dependency)

    if dependency.method == 'semver':
        dependency.rewrite(attribute='method', value='checkout',
            reason="Using lock file.")
        dependency.rewrite(attribute='checkout', value=checkout,
            reason="Using lock file.")
        dependency.rewrite(attribute='major', value=None,
            reason="Using lock file.")

    elif dependency.method == 'checkout':
        dependency.rewrite(attribute='checkout', value=checkout,
            reason="Using lock file.")

    else:
        raise Error("Unknown git dependency method {}".format(
            dependency.method))

    resolver = registry.require('resolve_chain',
        dependency=dependency)

    resolver = CheckLockCacheResolver(resolver=resolver, lock_cache=lock_cache,
        dependency=dependency)

    return resolver


@Registry.provide
def resolve_from_lock_path(registry, dependency):

    lock_cache = registry.require('lock_cache')

    dependency.rewrite(attribute='resolver', value='lock_path',
        reason="Using lock file.")

    resolver = registry.require('resolve_chain',
        dependency=dependency)

    resolver = CheckLockCacheResolver(resolver=resolver,
        lock_cache=lock_cache, dependency=dependency)

    return resolver


@Registry.provide
def resolve_lock_path(registry, dependency):

    lock_cache = registry.require('lock_cache')
    path = lock_cache.path(dependency=dependency)

    # Set the resolver method on the dependency
    dependency.resolver_action = 'lock path'

    return PathResolver(dependency=dependency, path=path)


@Registry.provide
def help_chain(registry, dependency):

    ctx = registry.require('ctx')
    resolve_config_path = registry.require('resolve_config_path')

    # Set the resolver action on the dependency
    dependency.resolver_chain = 'Load'
    dependency.resolver_action = 'help'

    resolver = OnPassiveLoadPathResolver(dependency=dependency,
        resolve_config_path=resolve_config_path)

    resolver = TryResolver(resolver=resolver, ctx=ctx)

    return resolver


@Registry.provide
def load_chain(registry, dependency):

    ctx = registry.require('ctx')
    resolve_config_path = registry.require('resolve_config_path')

    # Set the resolver action on the dependency
    dependency.resolver_chain = 'Load'

    resolver = OnPassiveLoadPathResolver(dependency=dependency,
        resolve_config_path=resolve_config_path)

    resolver = TryResolver(resolver=resolver, ctx=ctx)

    resolver = CheckOptionalResolver(resolver=resolver,
        dependency=dependency)

    return resolver


@Registry.provide
def resolve_chain(registry, dependency):

    ctx = registry.require('ctx')
    options = registry.require('options')
    resolve_config_path = registry.require('resolve_config_path')
    symlinks_path = registry.require('symlinks_path')
    configuration = registry.require('configuration')
    project_path = registry.require('project_path')

    # Set the resolver action on the dependency
    dependency.resolver_chain = 'Resolve'

    if options.path(dependency=dependency):
        resolver = registry.require('user_path_resolver', dependency=dependency)
    else:
        resolver_key = "resolve_{}".format(dependency.resolver)
        resolver = registry.require(resolver_key, dependency=dependency)

    resolver = CreateSymlinkResolver(
        resolver=resolver, dependency=dependency, symlinks_path=symlinks_path,
        ctx=ctx)

    resolver = OnActiveStorePathResolver(
        resolver=resolver, dependency=dependency,
        resolve_config_path=resolve_config_path)

    return resolver


@Registry.provide
def resolve_and_lock_chain(registry, dependency):

    resolver = registry.require('resolve_chain',
        dependency=dependency)

    project_path = registry.require('project_path')
    lock_cache = registry.require('lock_cache')
    lock_type = lock_cache.type()

    if lock_type == 'versions':
        return StoreLockVersionResolver(resolver=resolver,
            lock_cache=lock_cache, dependency=dependency)

    elif lock_type == 'paths':
        return StoreLockPathResolver(resolver=resolver,
            lock_cache=lock_cache, project_path=project_path,
            dependency=dependency)

    else:
        raise Error("Unknown lock type {}".format(lock_type))


@Registry.provide
def resolve_from_lock_chain(registry, dependency):

    lock_cache = registry.require('lock_cache')
    lock_type = lock_cache.type()

    if lock_type == 'versions':
        resolver_key = "resolve_from_lock_{}".format(
            dependency.resolver)
        resolver = registry.require(resolver_key, dependency=dependency)

    elif lock_type == 'paths':
        resolver = registry.require('resolve_from_lock_path',
            dependency=dependency)

    else:
        raise Error("Unknown lock type {}".format(lock_type))

    return resolver


@Registry.provide
def dependency_resolver(registry, dependency):
    """ Builds a WurfSourceResolver instance."""

    ctx = registry.require('ctx')

    # This is where we "wire" together the resolvers. Which actually do the
    # work of via some method obtaining a path to a dependency.
    #
    configuration = registry.require('configuration')
    resolver_key = "{}_chain".format(configuration.resolver_chain())

    resolver = registry.require(resolver_key, dependency=dependency)

    return ContextMsgResolver(resolver=resolver, ctx=ctx,
        dependency=dependency)


@Registry.provide
def configuration(registry):
    options = registry.require('options')
    args = registry.require('args')
    project_path = registry.require('project_path')

    return Configuration(options=options, args=args, project_path=project_path)


@Registry.provide
def dependency_manager(registry):

    # Clean the cache such that we get "fresh" objects
    registry.purge_cache()

    ctx = registry.require('ctx')
    dependency_cache = registry.require('dependency_cache')
    options = registry.require('options')

    return DependencyManager(registry=registry,
        dependency_cache=dependency_cache, ctx=ctx, options=options)


@Registry.provide
def resolve_lock_action(registry):

    lock_cache = registry.require('lock_cache')
    project_path = registry.require('project_path')

    def action():

        lock_path = os.path.join(project_path, Configuration.LOCK_FILE)
        lock_cache.write_to_file(lock_path)

    return action


@Registry.provide
def post_resolver_actions(registry):

    configuration = registry.require('configuration')

    actions = []

    if configuration.resolver_chain() == Configuration.RESOLVE_AND_LOCK:
        actions.append(registry.require('resolve_lock_action'))

    return actions


def build_registry(ctx, git_binary, default_resolve_path, resolve_config_path,
                   default_symlinks_path, semver,
                   waf_utils, args, project_path):
    """ Builds a registry.

    :param ctx: A Waf Context instance.
    :param git_binary: A string containing the path to a git executable.
    :param default_resolve_path: A string containing the path where the
        dependencies should be downloaded per default.
    :param resolve_config_path: A string containing the path to where the
        dependencies config json files should be / is stored.
    :param default_symlinks_path: A string containing the path where the
        dependency symlinks should be created per default.
    :param semver: The semver module
    :param waf_utils: The waflib.Utils module
    :param args: Argument strings as a list, typically this will come
        from sys.argv
    :param project_path: The path to the project as a string

    :returns:
        A new Registery instance.
    """
    registry = Registry()

    registry.provide_value('ctx', ctx)
    registry.provide_value('git_binary', git_binary)
    registry.provide_value('default_resolve_path', default_resolve_path)
    registry.provide_value('resolve_config_path', resolve_config_path)
    registry.provide_value('default_symlinks_path', default_symlinks_path)
    registry.provide_value('semver', semver)
    registry.provide_value('waf_utils', waf_utils)
    registry.provide_value('args', args)
    registry.provide_value('project_path', project_path)

    return registry
