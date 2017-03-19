#! /usr/bin/env python
# encoding: utf-8

# This file contains the methods added to the ConfigurationContext
# and BuildContext objects. This means that you can use these methods
# inside the configure(...) and build(...) functions defined in most
# wscripts.

from waflib.Configure import conf
from waflib import Logs

from . import waf_resolve_context


@conf
def dependency_path(ctx, name):
    """
    Returns the dependency path
    """
    return waf_resolve_context.dependency_cache[name]['path']


@conf
def is_toplevel(self):
    """
    Returns true if the current script is the top-level wscript
    """
    return self.srcnode == self.path


@conf
def recurse_dependencies(ctx):
    """ Recurse the dependencies which have the resolve property set to True.

    :param ctx: A Waf Context instance.
    """
    # Since dependency_cache is an OrderedDict, the dependencies will be
    # enumerated in the same order as they were defined in the wscripts
    # (waf-tools should be the first if it is defined)
    for name, dependency in waf_resolve_context.dependency_cache.items():

        if not dependency['recurse']:

            if Logs.verbose:
                Logs.debug('resolve: Skipped recurse for name={} cmd={}'.format(
                    name, ctx.cmd))

            continue

        path = dependency['path']

        if Logs.verbose:
            Logs.debug('resolve: recurse {} cmd={}, path={}'.format(
                name, ctx.cmd, path))

        # str() is needed as waf does not handle unicode in find_node
        ctx.recurse([str(path)], once=False, mandatory=False)
