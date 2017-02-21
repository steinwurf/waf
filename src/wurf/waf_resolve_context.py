#!/usr/bin/env python
# encoding: utf-8

import os
import sys
import argparse
import traceback

from collections import OrderedDict

from waflib import Utils
from waflib import Context
from waflib import Options
from waflib import Logs
from waflib import ConfigSet
from waflib import Node
from waflib.Configure import conf
from waflib.Errors import WafError

from . import registry
from .resolver_configuration import ResolverConfiguration
from .error import CmdAndLogError
from .error import Error

from waflib.extras import shutilwhich
from waflib.extras import semver


# To create the tree. https://gist.github.com/hrldcpr/2012250

dependency_cache = OrderedDict()
"""Dictionary that stores the dependencies resolved.

The dictionary will be initialized by the WafResolveContext and can be
used by all other contexts or tools that need to access the
dependencies. The idea is that this will be the single place to look to
figure out which dependencies exist.
"""

@conf
def recurse_dependencies(ctx):
    """ Recurse the dependencies which have the resolve property set to True.

    :param ctx: A Waf Context instance.
    """
    # Since dependency_cache is an OrderedDict, the dependencies will be
    # enumerated in the same order as they were defined in the wscripts
    # (waf-tools should be the first if it is defined)
    for name, dependency in dependency_cache.items():

        if not dependency['recurse']:

            ctx.to_log('Skipped recurse for name={} cmd={}\n'.format(
                name, ctx.cmd))

            continue

        ctx.to_log("Recurse for {}: cmd={}, path={}\n".format(
            name, ctx.cmd, dependency['path']))

        path = dependency['path']
        ctx.recurse([path], mandatory=False)


class WafResolveContext(Context.Context):

    '''resolves the dependencies specified in the wscript's resolve function'''

    cmd = 'resolve'
    fun = 'resolve'

    def __init__(self, **kw):
        """ Create a WafResolveContext
        """
        super(WafResolveContext, self).__init__(**kw)

    def execute(self):

        # Figure out which resolver configuration we should use, this has to
        # run before we create the build folder
        configuration = self.resolver_configuration()

        # Create the nodes that will be used during the resolve step. The build
        # directory is also used by the waf BuildContext
        self.srcnode = self.path
        self.bldnode = self.path.make_node('build')
        self.bldnode.mkdir()

        # Enable/disable colors based on the currently used terminal.
        # Note: this prevents jumbled output if waf is invoked from an IDE
        # that does not render colors in its output window
        Logs.enable_colors(1)
        path = os.path.join(self.bldnode.abspath(), configuration+'.resolve.log')
        self.logger = Logs.make_logger(path, 'cfg')

        self.logger.debug('wurf: Resolve execute {}'.format(configuration))

        # TODO: Do we really need the path to the git binary?
        #git_binary = shutilwhich.which('git')

        default_bundle_path = os.path.join(
            self.path.abspath(), 'bundle_dependencies')

        self.registry = registry.build_registry(
            ctx=self, git_binary='git',
            semver=semver, default_bundle_path=default_bundle_path,
            bundle_config_path=self.bundle_config_path(),
            resolver_configuration=configuration,
            waf_utils=Utils, args=sys.argv[1:])

        self.dependency_manager = self.registry.require('dependency_manager')

        # Calling the context execute will call the resolve(...) functions in
        # the wscripts. These will in turn call add_dependency(...) which will
        # trigger loading the dependency.

        try:
            super(WafResolveContext, self).execute()
        except Error as e:
            self.fatal("Error in resolve", ex=e)
        except:
            raise

        # Get the cache with the resolved dependencies
        global dependency_cache
        dependency_cache = self.registry.require('dependency_cache')

        self.logger.debug('wurf: dependency_cache {}'.format(dependency_cache))


    def is_toplevel(self):
        """
        Returns true if the current script is the top-level wscript
        """
        return self.srcnode == self.path


    def bundle_config_path(self):
        """Returns the bundle config path.

        The bundle config path will be used to store/load configuration for
        the different dependencies that are resolved.
        """

        return self.bldnode.abspath()


    def resolver_configuration(self):

        if '-h' in sys.argv or '--help' in sys.argv:
            return ResolverConfiguration.HELP
        elif 'configure' in sys.argv:
            # If active_resolvers, then the dependency resolvers are
            # allowed to download the dependencies.
            return ResolverConfiguration.ACTIVE
        elif not self.path.find_node('build'):
            # Project not yet configure - we don't have a build folder
            return ResolverConfiguration.HELP
        else:
            return ResolverConfiguration.PASSIVE

    def add_dependency(self, **kwargs):
        """Adds a dependency.
        """

        self.dependency_manager.add_dependency(**kwargs)

    def cmd_and_log(self, cmd, **kwargs):

        try:
            return super(WafResolveContext, self).cmd_and_log(
                cmd=cmd, **kwargs)
        except WafError as e:
            tb = traceback.format_exc()
            raise CmdAndLogError(error=e, traceback=tb)
        except:
            raise
