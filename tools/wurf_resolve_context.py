#!/usr/bin/env python
# encoding: utf-8

import os

from waflib import Utils
from waflib import Context
from waflib import Options
from waflib import Logs

from waflib.Configure import ConfigurationContext


class ResolveContext(ConfigurationContext):

    '''resolves the dependencies specified in the wscript's resolve function'''
    cmd = 'resolve'
    fun = 'resolve'

    def __init__(self, **kw):
        super(ResolveContext, self).__init__(**kw)

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
        self.load('wurf_common_tools')

        # Directly call Context.execute() to avoid the side effects of
        # ConfigurationContext.execute()
        Context.Context.execute(self)

        # Run the post_resolve function of wurf_dependency_bundle
        import waflib.extras.wurf_dependency_bundle as bundle
        bundle.post_resolve(self)
