#!/usr/bin/env python
# encoding: utf-8

from waflib import Context
from waflib import Utils

from waflib.Configure import ConfigurationContext


class WafConfigurationContext(ConfigurationContext):

    def __init__(self, **kw):
        super(WafConfigurationContext, self).__init__(**kw)

    def execute(self):
        # If the main wscript has no "configure" function, bind it to an
        # empty function. This allows us to omit configure.
        if 'configure' not in Context.g_module.__dict__:
            Context.g_module.configure = Utils.nada

        super(WafConfigurationContext, self).execute()

    def pre_recurse(self, node):

        super(WafConfigurationContext, self).pre_recurse(node)

        # Call configure() in all dependencies before executing configure()
        # in the top-level wscript: this allows us to configure the compiler
        # as a FIRST STEP using wurf_cxx_mkspec in waf-tools
        if self.is_toplevel():
            self.recurse_dependencies()
