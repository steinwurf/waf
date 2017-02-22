#! /usr/bin/env python
# encoding: utf-8

# This file contains the methods added to the ConfigurationContext
# and BuildContext objects. This means that you can use these methods
# inside the configure(...) and build(...) functions defined in most
# wscripts.

from waflib.Configure import conf

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

            ctx.to_log('Skipped recurse for name={} cmd={}\n'.format(
                name, ctx.cmd))

            continue

        ctx.to_log("Recurse for {}: cmd={}, path={}\n".format(
            name, ctx.cmd, dependency['path']))

        path = dependency['path']
        ctx.recurse([path], mandatory=False)
