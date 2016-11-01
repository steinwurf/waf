#! /usr/bin/env python
# encoding: utf-8

import inspect

import wurf_git
import wurf_git_url_resolver
import wurf_git_resolver
import wurf_git_checkout_resolver
import wurf_source_resolver
import wurf_user_checkout_resolver
import wurf_user_path_resolver

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

def build_wurf_git_method_resolver(registry):
    """ Builds a WurfGitMethodResolver instance."""

    user_methods = [registry.require('user_checkout_resolver')]

    git_methods = {
        'checkout': registry.require('git_checkout_resolver')}

    return wurf_source_resolver.WurfGitMethodResolver(
        user_methods=user_methods, git_methods=git_methods)

def build_wurf_user_checkout_resolver(registry):
    """ Builds a WurfUserCheckoutResolver instance."""

    git_checkout_resolver = registry.require('git_checkout_resolver')
    opt = registry.require('opt')

    return wurf_user_checkout_resolver.WurfUserCheckoutResolver(
        opt=opt, git_checkout_resolver=git_checkout_resolver)

def build_wurf_user_path_resolver(registry):
    """ Builds a WurfUserPathResolver instance."""

    opt = registry.require('opt')

    return wurf_user_path_resolver.WurfUserPathResolver(
        options_parser=opt)

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

def build_registry(ctx, opt, git_binary, bundle_path, bundle_config_path,
    active_resolve):
    """ Builds a registry.


    :param ctx: A Waf Context instance.
    :param opt: An argparse.ArgumentParser instance.
    :param git_binary: A string containing the path to a git executable.
    :param bundle_path: A string containing the path where dependencies should be
        downloaded.
    :param bundle_config_path: A string containing the path to where the
        dependencies config json files should be / is stored.
    :param active_resolve: Boolean which is True if this is an active resolve
        otherwise False.

    :returns:
        A new Registery instance.
    """

    registry = Registry()

    registry.provide_value('ctx', ctx)
    registry.provide_value('opt', opt)
    registry.provide_value('git_binary', git_binary)
    registry.provide_value('bundle_path', bundle_path)
    registry.provide_value('bundle_config_path', bundle_config_path)
    registry.provide_value('active_resolve', active_resolve)

    registry.provide('git', build_wurf_git)
    registry.provide('git_url_resolver', build_git_url_resolver)
    registry.provide('git_resolver', build_wurf_git_resolver)
    registry.provide('git_checkout_resolver', build_wurf_git_checkout_resolver)
    registry.provide('user_checkout_resolver', build_wurf_user_checkout_resolver)
    registry.provide('user_path_resolver', build_wurf_user_path_resolver)
    registry.provide('git_method_resolver', build_wurf_git_method_resolver)
    registry.provide('source_resolver', build_source_resolver)
    registry.provide('dependency_manager', build_dependency_manager)

    return registry
