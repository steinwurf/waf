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


def build_git_resolver(registry):
    git = registry.require('git')
    url_resolver = registry.require('git_url_resolver')
    log = registry.require('log')

    return wurf_git_resolver.WurfGitResolver(
        git=git, url_resolver=url_resolver, log=log)

def build_source_resolver(registry):

    source_resolvers = {'git': registry.require('git_resolver')}

    log = registry.require('log')

    return wurf_source_resolver.WurfSourceResolver(
        source_resolvers=source_resolvers, log=log)
        
def build_git(registry):

    context = registry.require('context')
    git_binary = registry.require('git_binary')
    
    return wurf_git.WurfGit(git_binary=git_binary, context=context)
    
def build_git_url_resolver(registry):
    
    return wurf_git_url_resolver.WurfGitUrlResolver()

def build_registry(ctx, log, git_binary):
    
    registry = Registry()
    
    registry.provide_value('context', ctx)
    registry.provide_value('git_binary', git_binary)
    registry.provide_value('log', log)
    registry.provide('git', build_git)
    registry.provide('git_url_resolver', build_git_url_resolver)
    registry.provide('git_resolver', build_git_resolver)
    registry.provide('source_resolver', build_source_resolver)
    
    return registry
    
    
