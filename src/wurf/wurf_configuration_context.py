#!/usr/bin/env python
# encoding: utf-8

from waflib.Configure import ConfigurationContext

from . import wurf_resolve_context


class WurfConfigurationContext(ConfigurationContext):


    def __init__(self, **kw):
        super(WurfConfigurationContext, self).__init__(**kw)

    def execute(self):

        super(WurfConfigurationContext, self).execute()

        # Call configure in all dependencies
        wurf_resolve_context.recurse_dependencies(self)
