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

from . import wurf_registry

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
    pass
    # for name, dependency in dependency_cache.items():
    #
    #     ctx.to_log("Recurse dependency {}".format(name))
    #
    #     if dependency.has_path() and dependency.requires_recurse():
    #
    #         ctx.to_log("Recurse for {}: cmd={}, path={}".format(
    #             name, ctx.cmd, dependency.path()))
    #
    #         ctx.recurse(dependency.path())
    #
    #     if ctx.cmd == 'options':
    #         dependency.add_options(ctx)


class WurfResolveContext(Context.Context):

    '''resolves the dependencies specified in the wscript's resolve function'''

    cmd = 'resolve'
    fun = 'resolve'

    def __init__(self, opt, **kw):
        """ Create a WurfResolveContext

        :param opt: A Waf options context instance.
        """
        super(WurfResolveContext, self).__init__(**kw)

        self.opt = opt

        # Store the options that will be passed to Waf's options parser
        self.waf_options = []


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

        # The resolve options
        self.parser = argparse.ArgumentParser(description='Resolve Options')

        bundle_path = os.path.join(self.path.abspath(), 'bundle_dependencies')

        # Using the %default placeholder:
        #    http://stackoverflow.com/a/1254491/1717320
        self.parser.add_argument('--bundle-path', default=bundle_path,
            dest='bundle_path',
            help='The folder where the bundled dependencies are downloaded.'
                 '[default: %default]')

        self.registry = wurf_registry.build_registry(
            ctx=self, opt=self.parser, git_binary=git_binary,
            semver=semver, bundle_path=self.bundle_path(),
            bundle_config_path=self.bundle_config_path(),
            active_resolve=self.is_active_resolve(), cache=dependency_cache)

        self.dependency_manager = self.registry.require('dependency_manager')

        # Directly call Context.execute() to avoid the side effects of
        # ConfigurationContext.execute()
        #
        # Calling the context execute will call the resolve(...) functions in
        # the wscripts. These will in turn call add_dependency(...) which will
        # trigger loading the dependency.

        super(WurfResolveContext, self).execute()

        # We are just interested in the left-over args, which is the second
        # value retuned by parse_known_args(...)
        _, self.waf_options = self.parser.parse_known_args()

        self.logger.debug('wurf: dependency_cache {}'.format(dependency_cache))


    def bundle_config_path(self):
        """Returns the bundle config path.

        The bundle config path will be used to store/load configuration for
        the different dependencies that are resolved.
        """

        return self.bldnode.abspath()

    def bundle_path(self):
        """Returns the bundle path.

        The bundle path is used by the different resolvers to download
        the dependencies i.e. it represents the path in the file system
        where all bundled dependencies are stored.
        """
        known_args, _ = self.parser.parse_known_args()

        bundle_path = os.path.abspath(os.path.expanduser(
            known_args.bundle_path))

        Utils.check_dir(bundle_path)

        return bundle_path

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
