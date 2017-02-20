#! /usr/bin/env python
# encoding: utf-8

# This file contains the methods added to the ConfigurationContext
# and BuildContext objects. This means that you can use these methods
# inside the configure(...) and build(...) functions defined in most
# wscripts.
# 

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
