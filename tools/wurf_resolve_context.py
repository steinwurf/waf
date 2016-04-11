#!/usr/bin/env python
# encoding: utf-8

import os
import sys

from waflib import Utils
from waflib import Context
from waflib import Options
from waflib import Logs
from waflib import ConfigSet

from waflib.Configure import ConfigurationContext

class WurfResolveContext(ConfigurationContext):

    '''resolves the dependencies specified in the wscript's resolve function'''
    cmd = 'resolve'
    fun = 'resolve'

    def __init__(self, **kw):
        super(WurfResolveContext, self).__init__(**kw)

    def load(self, tool_list, *k, **kw):

        # Directly call Context.load() to avoid the side effects of
        # ConfigurationContext.load()
        Context.Context.load(self, tool_list, *k, **kw)

    def execute(self):

        # Create the nodes that will be used during the resolve step
        self.srcnode = self.path
        self.bldnode = self.path.make_node('build')
        self.bldnode.mkdir()

        # Create a log file if this is an "active" resolve step
        if self.active_resolvers:
            path = os.path.join(self.bldnode.abspath(), 'resolve.log')
            self.logger = Logs.make_logger(path, 'cfg')

        # Make sure that the resolve function of the wurf_common_tools have
        # been executed. This removes the need for individual wscripts to
        # call ctx.load('wurf_common_tools')
        #
        # @todo lets remove th
        # self.load('wurf_common_tools')

        self.pre_resolve()

        print("WOT {}".format(self.env))

        # Directly call Context.execute() to avoid the side effects of
        # ConfigurationContext.execute()
        Context.Context.execute(self)

        # Run the post_resolve function of wurf_dependency_bundle
        #import waflib.extras.wurf_dependency_bundle as bundle
        #bundle.post_resolve(self)

        self.post_resolve()

    def pre_resolve(self):
        """ Load the environment from a previously completed resolve step
            or initialize a fresh one if this is an active resolve step"""

        if not self.active_resolvers:
            # Reload the environment from a previously completed resolve step
            # if resolve.config.py exists in the build directory
            try:
                path = os.path.join(self.bldnode.abspath(), 'resolve.config.py')
                self.env = ConfigSet.ConfigSet(path)
            except EnvironmentError as e:
                self.to_log(str(e))

            return

        # Create a dictionary to store the resolved dependency paths by name
        self.env['DEPENDENCY_DICT'] = dict()
        self.env['DEPENDENCY_LIST'] = list()

    def post_resolve(self):
        """ Store the environment after a resolve step. """

        if self.active_resolvers:

            # The dependency_dict will be needed in later steps
            #dependency_dict.update(ctx.env['DEPENDENCY_DICT'])

            # Save the environment that was created during the active
            # resolve step
            path = os.path.join(self.bldnode.abspath(), 'resolve.config.py')
            self.env.store(path)

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
        return os.path.join(self.path.abspath(), 'bundle_dependencies')


    def add_dependency(self, name, resolver, recurse=True, optional=False):
        """Adds a dependency.

        :param name: The name of the dependency. Must be unique.

        :param resolver: a resolver object which is responsible for downloading
                     the dependency if necessary
        :param recursive_resolve: specifies if it is allowed to recurse into the
        dependency wscript after the dependency is resolved
        :param optional: specifies if this dependency is optional (an optional
                     dependency might not be resolved if unavailable)
        """



        dependency = WurfDependency(name, resolver, recurse, optional)
