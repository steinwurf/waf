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

class Registry(object):

    def __init__(self):
        self.registry = {}

    def provide(self, feature, provider, **kwargs):

        def call(): return provider(registry=self, **kwargs)
        self.registry[feature] = call

    def provide_value(self, feature, value):

        def call(): return value
        self.registry[feature] = call

    def require(self, feature):
        call = self.registry[feature]
        return call()


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
    source_resolver = registry.require('source_resolver')

    return wurf_source_resolver.WurfActiveDependencyResolver(ctx=ctx,
        source_resolver=source_resolver)

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
    #
    registry.provide_value('parser', 
        argparse.ArgumentParser(description='Resolve Options'))

    # Dict object which will contain the path to the resolved
    # dependencies.
    registry.provide_value('cache', {})
    
    active_resolve = registry.require('active_resolve')
    
    if active_resolve:
        return build_active_dependency_manager(registry)
    else:
        return build_passive_dependency_manager(registry)
                    
def build_active_dependency_manager(registry):
    
    hash_manager = registry.require('hash_manager')
    skip_resolver = registry.require('skip_seen_dependency_resolver')
    bundle_path_resolver = registry.require('bundle_path_resolver')
    active_resolver = registry.require('active_dependency_resolver')
    store_resolver = registry.require('store_dependency_resolver')
    recurse_resolver = registry.require('recurse_dependency_resolver')
    cache_resolver = registry.require('cache_dependency_resolver')
    null_resolver = registry.require('null_dependency_resolver')

    hash_manager.next_resolver = skip_resolver
    skip_resolver.next_resolver = bundle_path_resolver
    bundle_path_resolver.next_resolver = active_resolver
    active_resolver.next_resolver = store_resolver
    store_resolver.next_resolver = recurse_resolver
    recurse_resolver.next_resolver = cache_resolver
    cache_resolver.next_resolver = null_resolver

    return hash_manager

def build_passive_dependency_manager(registry):

    hash_manager = registry.require('hash_manager')
    skip_resolver = registry.require('skip_seen_dependency_resolver')
    passive_resolver = registry.require('passive_dependency_resolver')
    recurse_resolver = registry.require('recurse_dependency_resolver')
    cache_resolver = registry.require('cache_dependency_resolver')
    null_resolver = registry.require('null_dependency_resolver')

    hash_manager.next_resolver = skip_resolver
    skip_resolver.next_resolver = passive_resolver
    passive_resolver.next_resolver = recurse_resolver
    recurse_resolver.next_resolver = cache_resolver
    cache_resolver.next_resolver = null_resolver

    return hash_manager

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
    registry.provide_value('parser', 
        argparse.ArgumentParser(description='Resolve Options'))
    registry.provide_value('git_binary', git_binary)
    registry.provide_value('default_bundle_path', default_bundle_path)
    registry.provide_value('bundle_config_path', bundle_config_path)
    registry.provide_value('active_resolve', active_resolve)
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
