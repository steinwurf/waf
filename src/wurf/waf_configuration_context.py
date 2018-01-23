#!/usr/bin/env python
# encoding: utf-8

import os

from waflib import Context
from waflib import Utils

from waflib.Configure import ConfigurationContext

from .symlink import create_symlink


class WafConfigurationContext(ConfigurationContext):

    def __init__(self, **kw):
        super(WafConfigurationContext, self).__init__(**kw)

    def init_dirs(self):

        # First call the configuration context init_dirs(..) function
        # which creates the actual folders.

        super(WafConfigurationContext, self).init_dirs()

        # Now create the symlink to where the build directory is. This gives
        # us a stable point in the filesystem from where we can always find
        # the bldnode directory.

        link_path = os.path.join(self.path.abspath(), 'build_current')

        create_symlink(from_path=self.bldnode.abspath(),
                       to_path=link_path, overwrite=True)

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
