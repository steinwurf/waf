#! /usr/bin/env python
# encoding: utf-8

import inspect

import wurf_git
import wurf_git_url_resolver
import wurf_git_resolver
import wurf_source_resolver

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

def build_source_resolver(registry):
    """ Builds a WurfSourceResolver instance."""

    source_resolvers = {'git': registry.require('git_resolver')}

    ctx = registry.require('ctx')

    return wurf_source_resolver.WurfSourceResolver(
        source_resolvers=source_resolvers, ctx=ctx)

def build_wurf_git(registry):
    """ Builds a WurfGit instance."""

    ctx = registry.require('ctx')
    git_binary = registry.require('git_binary')

    return wurf_git.WurfGit(git_binary=git_binary, ctx=ctx)

def build_git_url_resolver(registry):

    return wurf_git_url_resolver.WurfGitUrlResolver()

def build_dependency_manager(registry):

    ctx = registry.require('ctx')
    bundle_path = registry.require('bundle_path')
    bundle_config_path = registry.require('bundle_config_path')
    source_resolver = registry.require('source_resolver')

    return wurf_source_resolver.WurfActiveDependencyManager(
        ctx=ctx,
        bundle_path=bundle_path,
        bundle_config_path=bundle_config_path,
        source_resolver=source_resolver)

def build_registry(ctx, git_binary, bundle_path, bundle_config_path,
    active_resolve):
    """ Builds a registry.

    Args:
        ctx: A Waf Context instance.
        git_binary: A string containing the path to a git executable.
        bundle_path: A string containing the path where dependencies should be
            downloaded.
        bundle_config_path: A string containing the path to where the
            dependencies config json files should be / is stored.
        active_resolve: Boolean which is True if this is an active resolve
            otherwise False.

    Returns:
        A new Registery instance.
    """

    registry = Registry()

    registry.provide_value('ctx', ctx)
    registry.provide_value('git_binary', git_binary)
    registry.provide_value('bundle_path', bundle_path)
    registry.provide_value('bundle_config_path', bundle_config_path)
    registry.provide_value('active_resolve', active_resolve)

    registry.provide('git', build_wurf_git)
    registry.provide('git_url_resolver', build_git_url_resolver)
    registry.provide('git_resolver', build_wurf_git_resolver)
    registry.provide('source_resolver', build_source_resolver)
    registry.provide('dependency_manager', build_dependency_manager)

    return registry
