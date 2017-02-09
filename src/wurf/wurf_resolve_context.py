#!/usr/bin/env python
# encoding: utf-8

import os
import sys
import argparse

from waflib import Utils
from waflib import Context
from waflib import Options
from waflib import Logs
from waflib import ConfigSet
from waflib import Node

from . import registry

from waflib.extras import shutilwhich
from waflib.extras import semver


# To create the tree. https://gist.github.com/hrldcpr/2012250

dependency_cache = dict()
"""Dictionary that stores the dependencies resolved.

The dictionary will be initialized by the WurfResolveContext and can be
used by all other contexts or tools that need to access the
dependencies. The idea is that this will be the single place to look to
figure out which dependencies exist.
"""

def recurse_dependencies(ctx):
    """ Recurse the dependencies which have the resolve property set to True.

    :param ctx: A Waf Context instance.
    """

    for name, dependency in dependency_cache.items():

        if not dependency['recurse']:

            ctx.to_log('Skipped recurse for name={} cmd={}\n'.format(
                name, ctx.cmd))

            continue

        ctx.to_log("Recurse for {}: cmd={}, path={}\n".format(
            name, ctx.cmd, dependency['path']))

        path = dependency['path']

        ctx.to_log("Path {} Type {}\n".format(path, type(path)))
        ctx.recurse([path])


class WurfResolveContext(Context.Context):

    '''resolves the dependencies specified in the wscript's resolve function'''

    cmd = 'resolve'
    fun = 'resolve'

    def __init__(self, **kw):
        """ Create a WurfResolveContext
        """
        super(WurfResolveContext, self).__init__(**kw)

    def execute(self):

        # Create the nodes that will be used during the resolve step. The build
        # directory is also used by the waf BuildContext
        self.bldnode = self.path.make_node('build')
        self.bldnode.mkdir()

        # Create different log files depending on whether this is an "active"
        # resolve step

        if self.is_active_resolve():
            step = 'active'
        else:
            step = 'passive'

        path = os.path.join(self.bldnode.abspath(), step+'.resolve.log')
        self.logger = Logs.make_logger(path, 'cfg')

        self.logger.debug('wurf: Resolve execute')

        git_binary = shutilwhich.which('git')

        default_bundle_path = os.path.join(
            self.path.abspath(), 'bundle_dependencies')

        self.registry = registry.build_registry(
            ctx=self, git_binary=git_binary,
            semver=semver, default_bundle_path=default_bundle_path,
            bundle_config_path=self.bundle_config_path(),
            active_resolve=self.is_active_resolve(),
            utils=Utils, args=sys.argv[1:])

        print("RESOLVE CONTEXT")
        self.dependency_manager = self.registry.require('dependency_manager')

        # Calling the context execute will call the resolve(...) functions in
        # the wscripts. These will in turn call add_dependency(...) which will
        # trigger loading the dependency.

        super(WurfResolveContext, self).execute()

        # Get the cache with the resolved dependencies
        global dependency_cache
        dependency_cache = self.registry.require('cache')

        self.logger.debug('wurf: dependency_cache {}'.format(dependency_cache))


    def bundle_config_path(self):
        """Returns the bundle config path.

        The bundle config path will be used to store/load configuration for
        the different dependencies that are resolved.
        """

        return self.bldnode.abspath()


    def is_active_resolve(self):

        show_help = '-h' in sys.argv or '--help' in sys.argv

        # If active_resolvers is true, then the dependency resolvers are
        # allowed to download the dependencies. If it is false, then the
        # dependency bundle will only recurse into the previously resolved
        # dependencies to fetch the options from these.
        return 'configure' in sys.argv and not show_help


    def add_dependency(self, **kwargs):
        """Adds a dependency.
        """

        self.dependency_manager.add_dependency(**kwargs)
