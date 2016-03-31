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
