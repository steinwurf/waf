#! /usr/bin/env python
# encoding: utf-8

import argparse
import os
import json
import hashlib
import inspect
import collections

from .archive_resolver import ArchiveResolver
from .check_lock_cache_resolver import CheckLockCacheResolver
from .config_file import ConfigFile
from .configuration import Configuration
from .context_msg_resolver import ContextMsgResolver
from .create_symlink_resolver import CreateSymlinkResolver
from .dependency_manager import DependencyManager
from .git_existing_checkout_resolver import GitExistingCheckoutResolver
from .git import Git
from .git_checkout_resolver import GitCheckoutResolver
from .git_resolver import GitResolver
from .git_semver_resolver import GitSemverResolver
from .git_url_parser import GitUrlParser
from .git_url_rewriter import GitUrlRewriter
from .http_resolver import HttpResolver
from .list_resolver import ListResolver
from .lock_path_cache import LockPathCache
from .lock_version_cache import LockVersionCache
from .mandatory_options import MandatoryOptions
from .mandatory_resolver import MandatoryResolver
from .on_active_store_path_resolver import OnActiveStorePathResolver
from .on_passive_load_path_resolver import OnPassiveLoadPathResolver
from .options import Options
from .path_resolver import PathResolver
from .post_resolve_run import PostResolveRun
from .semver_selector import SemverSelector
from .store_lock_path_resolver import StoreLockPathResolver
from .store_lock_version_resolver import StoreLockVersionResolver
from .try_resolver import TryResolver
from .url_download import UrlDownload

from .error import WurfError


class RegistryProviderError(WurfError):
    """Exception used by the Registry"""

    def __init__(self, name):
        self.name = name
        super(RegistryProviderError, self).__init__(
            f"Registry error: {self.name} already added to registry"
        )


class RegistryInjectError(WurfError):
    def __init__(self, provider_function, missing_provider):
        self.provider_function = provider_function
        self.missing_provider = missing_provider

        super(RegistryInjectError, self).__init__(
            f'Fatal error provider "{self.provider_function.__name__}" '
            f'requires "{self.missing_provider}"'
        )


class RegistryCacheOnceError(WurfError):
    def __init__(self, provider_name, provider_function):
        self.provider_name = provider_name
        self.provider_function = provider_function

        super(RegistryCacheOnceError, self).__init__(
            f'Fatal error provider "{self.provider_name}" should only be cached once. '
            f'The provided values passed to "{self.provider_function.__name__}" '
            f"have changed since the object was initially cached."
        )


class Registry(object):
    # The TemporaryValue is used to provide temporary values though the
    # registry.
    #
    # Example:
    #
    #    with registry.provide_temporary as tmp:
    #        tmp.provide_value('temperature', 'hot!'):
    #        assert registry.require('temperature') == 'hot!'
    #
    #    assert 'temperature' not in registry
    #
    # The TemporaryValue is returned by the provide_temporary function and
    # ensures that the value is removed from the registry after the "with"
    # block is finished.
    class TemporaryValue:
        def __init__(self, registry):
            self.registry = registry
            self.provider_names = []

        def __enter__(self):
            return self

        def provide_value(self, provider_name, value, override=False):
            self.provider_names.append(provider_name)

            self.registry.provide_value(
                provider_name=provider_name, value=value, override=override
            )

        def __exit__(self, type, value, traceback):
            for provider_name in self.provider_names:
                self.registry.remove(provider_name=provider_name)

    ShouldCache = collections.namedtuple("ShouldCache", "name once")

    class CacheEntry(object):
        def __init__(self, once):
            self.once = once
            self.data = {}

    # Dictionary containing the provider functions registered
    # using the @Registry.provide decorator
    providers = {}

    # Set which will track which provider functions that produce values
    # that should be cached. This is done using @Registry.cache decorator.
    cache_providers = set()

    def __init__(self, use_providers=True, use_cache_providers=True):
        """
        :param use_providers: True if the class providers should be added.
            False will create a new Registry instance without any added
            providers.
        """
        # Dictionary which will contain the feature as a key and a
        # provider function as value
        self.registry = {}

        # Dictionary which contains cached values produced for the different
        # providers. The layout of the dictionary will be:
        # { 'provider1': { argument_hash1: value1,
        #                  argument_hash2: value2 },
        #   'provider2': { argument_hash1: value1 },
        #   ....
        # }
        #
        # Where the provider name is the key to a dictionary where cached
        # values are stored. The nested dict uses a hash of the arguments
        # passed to require(...) to find the right cached response.
        self._cache = {}

        # Set which contains the name of features that should be cached
        if use_cache_providers:
            for s in Registry.cache_providers:
                self.cache_provider(provider_name=s.name, once=s.once)

        if use_providers:
            for k, v in Registry.providers.items():
                self.provide_function(k, v)

    def cache_provider(self, provider_name, once):
        """Specify that objects / values produced by the provider should be
            cached.

        :param provider_name: The provider's name as a string
        """
        assert provider_name not in self._cache
        self._cache[provider_name] = Registry.CacheEntry(once=once)

    def purge_cache(self):
        """Empty the registry cache."""
        for provider_name in self._cache:
            self._cache[provider_name].data = {}

    def __inject_arguments(self, provider_function):
        """Based on function signature prepare arguments.

        This function takes as input a function object, based on the
        arguments it builds a dictionary object which can be used
        to call the function. The arguments values are found in the
        registry.

        :param provider_function: The function object which we would
           like to call
        :return: Dictionary containing the arguments and corresponding values.
        """

        inject_arguments = {}
        require_arguments = inspect.getfullargspec(provider_function)[0]

        for argument in require_arguments:
            if argument == "registry":
                inject_arguments[argument] = self
                continue

            if argument not in self:
                raise RegistryInjectError(
                    provider_function=provider_function, missing_provider=argument
                )

            inject_arguments[argument] = self.require(argument)

        return inject_arguments

    def __hash_arguments(self, arguments):
        """
        Provides a hash of the arguments to be passed to a provider function.

        The hash is used to make sure the registry provides stable cached
        results.
        """

        hash_dict = {}
        for k, v in arguments.items():
            if isinstance(v, (list, tuple, dict, set)):
                hash_dict[k] = hash(json.dumps(v, sort_keys=True))
            else:
                hash_dict[k] = hash(v)

        return hash(json.dumps(hash_dict, sort_keys=True))

    def provide_function(self, provider_name, provider_function, override=False):
        """
        :param provider_name: The name of the provider as a string
        :param provider_function: Function to call which will provide the value
        :param cache: Determines whether calls to the provider should be
            cached.
            If arguments are passed to the provider in the require(...)
            function, they must be hashable.
        :param override: Determines whether the provider should
            override/replace an existing provider. If True we will override an
            existing provider with the same name.
        """
        if not override and provider_name in self.registry:
            raise RegistryProviderError(provider_name)

        def call():
            inject_arguments = self.__inject_arguments(
                provider_function=provider_function
            )

            # Did we already cache?
            if provider_name in self._cache:
                key = self.__hash_arguments(inject_arguments)

                provider = self._cache[provider_name]

                try:
                    return provider.data[key]
                except KeyError:
                    if provider.once and len(provider.data) > 0:
                        raise RegistryCacheOnceError(provider_name, provider_function)

                    result = provider_function(**inject_arguments)
                    provider.data[key] = result
                    return result
            else:
                result = provider_function(**inject_arguments)
                return result

        self.registry[provider_name] = call

        if provider_name in self._cache:
            # Clean the cache
            self._cache[provider_name].data = {}

    def provide_temporary(self):
        """:return: Temporary context which allows can be used to provide
        temporary values.
        """
        return Registry.TemporaryValue(registry=self)

    def provide_value(self, provider_name, value, override=False):
        """
        :param provider_name: The name of the provider as a string
        :param value: The value with should be returned on require(...)
        :param override: Determines whether the provider should
            override/replace an existing provider. If True we will override an
            existing provider with the same name.
        """
        if not override and provider_name in self.registry:
            raise RegistryProviderError(provider_name)

        def call():
            return value

        self.registry[provider_name] = call

    def require(self, provider_name):
        """
        :param provider_name: The name of the provider as a string
        """
        if inspect.isclass(provider_name):
            provider_name = provider_name.__name__
        if inspect.isfunction(provider_name):
            provider_name = provider_name.__name__

        call = self.registry[provider_name]
        return call()

    def remove(self, provider_name):
        """
        :param provider_name: The name of the provider as a string
        """
        if provider_name in self._cache:
            del self._cache[provider_name]

        # The provider must exist in the registry
        del self.registry[provider_name]

    def __contains__(self, provider_name):
        """
        :param provider_name: The name of the provider as a string
        :return: True if the provider is in the registry
        """
        return provider_name in self.registry

    @staticmethod
    def cache(func):
        Registry.cache_providers.add(
            Registry.ShouldCache(name=func.__name__, once=False)
        )
        return func

    @staticmethod
    def cache_once(func):
        Registry.cache_providers.add(
            Registry.ShouldCache(name=func.__name__, once=True)
        )
        return func

    @staticmethod
    def provide(func):
        if func.__name__ in Registry.providers:
            raise RegistryProviderError(func.__name__)
        Registry.providers[func.__name__] = func

        return func


@Registry.cache_once
@Registry.provide
def resolve_path(mandatory_options, waf_utils):
    resolve_path = mandatory_options.resolve_path()
    resolve_path = os.path.abspath(os.path.expanduser(resolve_path))

    waf_utils.check_dir(resolve_path)

    return resolve_path


@Registry.cache_once
@Registry.provide
def symlinks_path(mandatory_options, waf_utils):
    symlinks_path = mandatory_options.symlinks_path()
    symlinks_path = os.path.abspath(os.path.expanduser(symlinks_path))

    waf_utils.check_dir(symlinks_path)

    return symlinks_path


@Registry.cache
@Registry.provide
def dependency_path(git_url_rewriter, resolve_path, dependency, waf_utils):
    if dependency.resolver == "git":
        repo_url = git_url_rewriter.rewrite_url(url=dependency.source)
        repo_hash = hashlib.sha1(repo_url.encode("utf-8")).hexdigest()[:6]
        name = dependency.name + "-" + repo_hash
    else:
        source_hash = hashlib.sha1(dependency.source.encode("utf-8")).hexdigest()[:6]
        name = dependency.name + "-" + source_hash

    dependency_path = os.path.join(resolve_path, name)
    waf_utils.check_dir(dependency_path)

    return dependency_path


@Registry.cache_once
@Registry.provide
def git_url_parser():
    """Parser for Git URLs."""
    return GitUrlParser()


@Registry.cache_once
@Registry.provide
def git_url_rewriter(git_url_parser, git_protocol):
    """Rewriter for Git URLs.

    Supports various transformations such as changing/adding the git
    protocol.
    """
    return GitUrlRewriter(parser=git_url_parser, rewrite_protocol=git_protocol)


@Registry.cache_once
@Registry.provide
def parser():
    return argparse.ArgumentParser(
        description="Resolve Options",
        # add_help=False will remove the default handling of --help and -h
        # https://docs.python.org/3/library/argparse.html#add-help
        # This will be handled by waf's default options context.
        add_help=False,
    )


@Registry.cache_once
@Registry.provide
def dependency_cache():
    return collections.OrderedDict()


@Registry.cache_once
@Registry.provide
def lock_cache_from(git, configuration, project_path):
    resolver_chain = configuration.resolver_chain()
    if resolver_chain == Configuration.RESOLVE_FROM_PATH_LOCK:
        return LockPathCache.create_from_file(cwd=project_path)
    elif resolver_chain == Configuration.RESOLVE_FROM_VERSION_LOCK:
        return LockVersionCache.create_from_file(git=git, cwd=project_path)
    else:
        raise WurfError(f"Lock cache not available for {resolver_chain} chain")


@Registry.cache_once
@Registry.provide
def lock_cache_to(git, configuration: Configuration):
    if configuration.lock_paths():
        return LockPathCache.create_empty()
    elif configuration.lock_versions():
        return LockVersionCache.create_empty(git=git)
    else:
        raise WurfError("Lock cache not available")


@Registry.cache_once
@Registry.provide
def options(parser, args, default_resolve_path, default_symlinks_path, config_file):
    """Return the Options provider."""

    # We support the protocols we know how to rewrite
    supported_git_protocols = GitUrlRewriter.git_protocols.keys()

    if config_file.default_resolve_path:
        resolve_path = config_file.default_resolve_path
    else:
        resolve_path = default_resolve_path

    return Options(
        args=args,
        parser=parser,
        default_resolve_path=resolve_path,
        default_symlinks_path=default_symlinks_path,
        supported_git_protocols=supported_git_protocols,
    )


@Registry.cache_once
@Registry.provide
def config_file(ctx):
    """Return the ConfigFile provider."""

    return ConfigFile(ctx=ctx)


@Registry.cache_once
@Registry.provide
def mandatory_options(options):
    """Return the MandatoryOptions provider."""
    return MandatoryOptions(options=options)


@Registry.cache_once
@Registry.provide
def semver_selector(semver):
    """Return the SemverSelector provider."""
    return SemverSelector(semver=semver)


@Registry.cache_once
@Registry.provide
def url_download():
    """Return the UrlDownload provider."""
    return UrlDownload()


@Registry.cache_once
@Registry.provide
def project_git_protocol(git, ctx, git_url_parser):
    """Return the Git protocol used by the parent project.

    If parent project not under git version control return None.
    """
    try:
        parent_url = git.remote_origin_url(cwd=os.getcwd())

    except Exception as e:
        ctx.to_log(f"Exception when executing git.remote_origin_url: {e}")
        return None

    try:
        url = git_url_parser.parse(parent_url)
        return url.protocol

    except Exception as e:
        ctx.to_log(f"Exception could not parse git URL {parent_url} error: {e}")
        return None


@Registry.cache_once
@Registry.provide
def git(git_binary, ctx):
    """The Git object, which is used to run git commands."""
    return Git(git_binary=git_binary, ctx=ctx)


@Registry.cache_once
@Registry.provide
def git_protocol(options, project_git_protocol):
    """Return the Git protocol to use."""

    # Check if the user specified a git protocol to use:
    protocol = options.git_protocol()

    # Check what the parent project uses
    if not protocol:
        protocol = project_git_protocol

    # Finally just use https
    if not protocol:
        protocol = "https://"

    return protocol


@Registry.provide
def post_resolve(registry, current_resolver, dependency):
    """Add the post resolve steps"""

    resolver = current_resolver

    for action in dependency.post_resolve:
        with registry.provide_temporary() as temporary:
            temporary.provide_value(f'{action["type"]}_command', action["command"])

            if action["type"] != "run":
                raise NotImplementedError(
                    f"Post resolve action {action['type']} specified for "
                    f"{dependency.name} not supported"
                )

            resolver = registry.require("post_resolve_run")

        registry.provide_value(
            provider_name="current_resolver", value=resolver, override=True
        )

    return resolver


@Registry.provide
def user_path_resolver(mandatory_options, dependency):
    path = mandatory_options.path(dependency=dependency)

    # Set the resolver method on the dependency
    dependency.resolver_action = "user path"

    return PathResolver(dependency=dependency, path=path)


@Registry.provide
def post_resolve_run(current_resolver, ctx, run_command, dependency_path):
    return PostResolveRun(
        resolver=current_resolver, ctx=ctx, run=run_command, cwd=dependency_path
    )


@Registry.provide
def git_resolver(git, ctx, dependency, git_url_rewriter, dependency_path):
    """Builds a GitResolver instance.

    :param registry: A Registry instance.
    """
    return GitResolver(
        git=git,
        ctx=ctx,
        dependency=dependency,
        git_url_rewriter=git_url_rewriter,
        cwd=dependency_path,
    )


@Registry.provide
def git_checkout_resolver(
    registry, git, git_resolver, ctx, dependency, dependency_path
):
    """Builds a GitResolver instance.

    :param registry: A Registry instance.
    """
    if "checkout" in registry:
        checkout = registry.require("checkout")
    else:
        checkout = dependency.checkout

    return GitCheckoutResolver(
        git=git,
        resolver=git_resolver,
        ctx=ctx,
        dependency=dependency,
        checkout=checkout,
        cwd=dependency_path,
    )


@Registry.provide
def git_existing_checkout_resolver(
    registry, ctx, git, dependency, git_checkout_resolver, dependency_path
):
    """Builds a GitResolver instance.

    :param registry: A Registry instance.
    """

    if "checkout" in registry:
        checkout = registry.require("checkout")
    else:
        checkout = dependency.checkout

    return GitExistingCheckoutResolver(
        ctx=ctx,
        git=git,
        dependency=dependency,
        resolver=git_checkout_resolver,
        checkout=checkout,
        cwd=dependency_path,
    )


@Registry.provide
def resolve_git_checkout(git_existing_checkout_resolver, dependency):
    """Builds a WurfGitCheckoutResolver instance.

    :param registry: A Registry instance.
    :param dependency: A Dependency instance.
    """

    # Set the resolver method on the dependency
    dependency.resolver_action = "git checkout"

    return git_existing_checkout_resolver


@Registry.provide
def resolve_git_user_checkout(registry, mandatory_options, dependency):
    """Builds resolver that uses a user specified checkout.

    :param registry: A Registry instance.
    :param dependency: A Dependency instance.
    """
    checkout = mandatory_options.checkout(dependency=dependency)

    with registry.provide_temporary() as temporary:
        temporary.provide_value("checkout", checkout)

        # When the user specified the checkout one must succeed:
        resolver = registry.require("resolve_git_checkout")

        resolver = MandatoryResolver(
            resolver=resolver,
            msg=f"User checkout of '{checkout}' failed.",
            dependency=dependency,
        )

    # Set the resolver action on the dependency
    dependency.resolver_action = "git user checkout"

    return resolver


@Registry.provide
def resolve_git_semver(registry, dependency):
    """Builds a GitSemverResolver instance.
    :param registry: A Registry instance.
    :param dependency: A WurfDependency instance.
    """
    resolver = registry.require("git_semver_resolver")

    # Set the resolver action on the dependency
    dependency.resolver_action = "git semver"

    return resolver


@Registry.provide
def git_semver_resolver(
    git, git_resolver, ctx, semver_selector, dependency, dependency_path
):
    """Builds a GitResolver instance.

    :param registry: A Registry instance.
    """
    return GitSemverResolver(
        ctx=ctx,
        git=git,
        resolver=git_resolver,
        semver_selector=semver_selector,
        dependency=dependency,
        cwd=dependency_path,
    )


@Registry.provide
def resolve_git(registry, options, dependency):
    """Builds git resolvers

    :param registry: A Registry instance.
    :param dependency: A WurfDependency instance.
    """

    checkout = options.checkout(dependency=dependency)
    if checkout:
        method = "user_checkout"
    if "method" in registry:
        method = registry.require("method")
    else:
        method = dependency.method

    resolver_keys = {
        "checkout": "resolve_git_checkout",
        "semver": "resolve_git_semver",
        "user_checkout": "resolve_git_user_checkout",
    }
    resolver_key = resolver_keys.get(method, None)
    if resolver_key is None:
        raise WurfError(f"Unknown git resolver method {method}")

    return registry.require(resolver_key)


@Registry.cache
@Registry.provide
def resolve_http(
    archive_extractor,
    url_download,
    dependency,
    dependency_path,
):
    dependency.resolver_action = "http"

    resolver = HttpResolver(
        url_download=url_download,
        dependency=dependency,
        cwd=dependency_path,
    )

    if dependency.extract:
        resolver = ArchiveResolver(
            archive_extractor=archive_extractor, resolver=resolver, cwd=dependency_path
        )

    return resolver


@Registry.provide
def resolve_locked_version(registry, git, ctx, dependency, resolve_path):
    # Set the resolver action on the dependency
    resolver = registry.require(f"resolve_{dependency.resolver}")
    dependency.resolver_action = f"lock/{dependency.resolver_action}"

    resolve_config_path = registry.require("resolve_config_path")

    lock_resolver = OnPassiveLoadPathResolver(
        git=git,
        dependency=dependency,
        resolve_config_path=resolve_config_path,
        resolve_path=resolve_path,
    )
    lock_resolver = TryResolver(resolver=lock_resolver, ctx=ctx, dependency=dependency)

    return ListResolver(resolvers=[lock_resolver, resolver])


@Registry.provide
def resolve_locked_path(lock_cache_from: LockPathCache, dependency):
    path = lock_cache_from.path(dependency=dependency)

    # Set the resolver action on the dependency
    dependency.resolver_action = "locked path"

    return PathResolver(dependency=dependency, path=path)


@Registry.provide
def help_chain(ctx, git, resolve_config_path, dependency, resolve_path):
    # Set the resolver action on the dependency
    dependency.resolver_chain = "Load"
    dependency.resolver_action = "help"

    resolver = OnPassiveLoadPathResolver(
        git=git,
        dependency=dependency,
        resolve_config_path=resolve_config_path,
        resolve_path=resolve_path,
    )

    return TryResolver(resolver=resolver, ctx=ctx, dependency=dependency)


@Registry.provide
def load_chain(ctx, git, resolve_config_path, dependency, resolve_path):
    # Set the resolver chain on the dependency
    dependency.resolver_chain = "Load"

    resolver = OnPassiveLoadPathResolver(
        git=git,
        dependency=dependency,
        resolve_config_path=resolve_config_path,
        resolve_path=resolve_path,
    )

    resolver = TryResolver(resolver=resolver, ctx=ctx, dependency=dependency)

    return MandatoryResolver(
        resolver=resolver, msg="Dependency failed.", dependency=dependency
    )


@Registry.provide
def source_resolver(ctx, registry, dependency):
    with registry.provide_temporary() as temporary:
        # The resolver to be used for a dependency can be overridden
        # and example of this is when resolving from a lock path.
        if "resolver" in registry:
            resolver = registry.require("resolver")
        else:
            resolver = dependency.resolver

        resolver_keys = {
            "git": "resolve_git",
            "http": "resolve_http",
            "locked_path": "resolve_locked_path",
            "locked_version": "resolve_locked_version",
        }

        resolver_key = resolver_keys.get(resolver, None)
        if resolver_key is None:
            raise WurfError(f"Unknown resolver {resolver}")

        resolver = registry.require(resolver_key)

        if dependency.post_resolve is not None:
            # Add the post resolve
            temporary.provide_value("current_resolver", resolver)
            resolver = registry.require("post_resolve")

    resolver = TryResolver(resolver=resolver, ctx=ctx, dependency=dependency)
    return MandatoryResolver(
        resolver=resolver, msg="Dependency failed.", dependency=dependency
    )


@Registry.provide
def resolve_chain(
    ctx, options, registry, dependency, resolve_config_path, symlinks_path
):
    # Set the resolver chain on the dependency
    dependency.resolver_chain = "Resolve"

    if options.path(dependency=dependency):
        if options.lock_versions():
            raise WurfError(
                f'A user path has been specified for "{dependency.name}". '
                "Setting a user path is not supported when locking versions."
            )

        resolver = registry.require("user_path_resolver")
    else:
        with registry.provide_temporary() as temporary:
            if dependency.locked_version is not None:
                temporary.provide_value("resolver", "locked_version")

            resolver = registry.require("source_resolver")

    resolver = CreateSymlinkResolver(
        resolver=resolver, dependency=dependency, symlinks_path=symlinks_path, ctx=ctx
    )

    resolver = OnActiveStorePathResolver(
        resolver=resolver,
        dependency=dependency,
        resolve_config_path=resolve_config_path,
    )

    return resolver


@Registry.provide
def store_lock_version_resolver(store_resolver, dependency, lock_cache_to):
    return StoreLockVersionResolver(
        resolver=store_resolver, lock_cache_to=lock_cache_to, dependency=dependency
    )


@Registry.provide
def store_lock_path_resolver(store_resolver, dependency, project_path, lock_cache_to):
    return StoreLockPathResolver(
        resolver=store_resolver,
        lock_cache_to=lock_cache_to,
        project_path=project_path,
        dependency=dependency,
    )


@Registry.provide
def resolve_from_version_lock_chain(registry, lock_cache_from, dependency):
    with registry.provide_temporary() as temporary:
        if dependency.resolver == "git":
            commit_id = lock_cache_from.commit_id(dependency=dependency)
            temporary.provide_value("checkout", commit_id)
            temporary.provide_value("method", "checkout")
        resolver = registry.require("resolve_chain")

    return CheckLockCacheResolver(
        resolver=resolver, lock_cache_from=lock_cache_from, dependency=dependency
    )


@Registry.provide
def resolve_from_path_lock_chain(registry, lock_cache_from, dependency):
    with registry.provide_temporary() as temporary:
        temporary.provide_value("resolver", "locked_path")
        resolver = registry.require("resolve_chain")

    return CheckLockCacheResolver(
        resolver=resolver, lock_cache_from=lock_cache_from, dependency=dependency
    )


@Registry.provide
def dependency_resolver(registry, ctx, configuration: Configuration, dependency):
    """Builds a ContextMsgResolver instance."""

    # This is where we "wire" together the resolvers. Which actually do the
    # work of via some method obtaining a path to a dependency.
    resolver_keys = {
        Configuration.HELP: "help_chain",
        Configuration.RESOLVE_FROM_PATH_LOCK: "resolve_from_path_lock_chain",
        Configuration.RESOLVE_FROM_VERSION_LOCK: "resolve_from_version_lock_chain",
        Configuration.RESOLVE: "resolve_chain",
        Configuration.LOAD: "load_chain",
    }

    resolver_key = resolver_keys.get(configuration.resolver_chain(), None)
    if resolver_key is None:
        raise WurfError(f"Unknown resolver chain {configuration.resolver_chain()}")

    resolver = registry.require(resolver_key)

    if configuration.lock_paths():
        with registry.provide_temporary() as temporary:
            temporary.provide_value("store_resolver", resolver)
            resolver = registry.require("store_lock_path_resolver")
    elif configuration.lock_versions():
        if configuration.resolver_chain() == Configuration.RESOLVE_FROM_PATH_LOCK:
            raise WurfError(
                "Locking versions is not supported when using locked paths. "
                "Remove the lock_path_resolve.json file and try again."
            )
        if configuration.resolver_chain() == Configuration.RESOLVE_FROM_VERSION_LOCK:
            raise WurfError(
                "Locking versions is not supported when using locked versions. "
                "Remove the lock_version_resolve.json file and try again."
            )
        with registry.provide_temporary() as temporary:
            temporary.provide_value("store_resolver", resolver)
            resolver = registry.require("store_lock_version_resolver")

    return ContextMsgResolver(resolver=resolver, ctx=ctx, dependency=dependency)


@Registry.cache_once
@Registry.provide
def configuration(options, args, project_path, waf_lock_file):
    return Configuration(
        options=options,
        args=args,
        project_path=project_path,
        waf_lock_file=waf_lock_file,
    )


@Registry.provide
def dependency_manager(registry):
    # Clean the cache such that we get "fresh" objects
    registry.purge_cache()

    ctx = registry.require("ctx")
    git = registry.require("git")
    dependency_cache = registry.require("dependency_cache")
    options = registry.require("options")
    skip_internal = registry.require("skip_internal")

    return DependencyManager(
        registry=registry,
        dependency_cache=dependency_cache,
        ctx=ctx,
        git=git,
        options=options,
        skip_internal=skip_internal,
    )


@Registry.provide
def resolve_lock_action(lock_cache_to, project_path):
    def action():
        lock_cache_to.write_to_file(cwd=project_path)

    return action


@Registry.provide
def post_resolver_actions(registry, configuration: Configuration):
    actions = []

    if configuration.lock_paths() or configuration.lock_versions():
        actions.append(registry.require("resolve_lock_action"))

    return actions


def resolve_registry(
    ctx,
    git_binary,
    default_resolve_path,
    resolve_config_path,
    default_symlinks_path,
    semver,
    archive_extractor,
    waf_utils,
    args,
    project_path,
    waf_lock_file,
    skip_internal,
):
    """Builds a registry.

    :param ctx: A Waf Context instance.
    :param git_binary: A string containing the path to a git executable.
    :param default_resolve_path: A string containing the path where the
        dependencies should be downloaded per default.
    :param resolve_config_path: A string containing the path to where the
        dependencies config json files should be / is stored.
    :param default_symlinks_path: A string containing the path where the
        dependency symlinks should be created per default.
    :param semver: The semver module
    :param archive_extractor: An archive (zip, tar, etc.) extractor function.
    :param waf_utils: The waflib.Utils module
    :param args: Argument strings as a list, typically this will come
        from sys.argv
    :param project_path: The path to the project as a string
    :param waf_lock_file: The lock file created by waf after a successful
        configure.
    :param skip_internal: A flag specifying whether internal dependencies
        should be skipped.
    :returns:
        A new Registry instance.
    """
    registry = Registry()

    registry.provide_value("ctx", ctx)
    registry.provide_value("git_binary", git_binary)
    registry.provide_value("default_resolve_path", default_resolve_path)
    registry.provide_value("resolve_config_path", resolve_config_path)
    registry.provide_value("default_symlinks_path", default_symlinks_path)
    registry.provide_value("semver", semver)
    registry.provide_value("archive_extractor", archive_extractor)
    registry.provide_value("waf_utils", waf_utils)
    registry.provide_value("args", args)
    registry.provide_value("project_path", project_path)
    registry.provide_value("waf_lock_file", waf_lock_file)
    registry.provide_value("skip_internal", skip_internal)

    return registry


def options_registry(ctx, git_binary):
    """Builds a registry.

    :param ctx: A Waf Context instance.
    :param git_binary: A string containing the path to a git executable.


    :returns:
        A new Registry instance.
    """
    registry = Registry()

    registry.provide_value("ctx", ctx)
    registry.provide_value("git_binary", git_binary)

    return registry
