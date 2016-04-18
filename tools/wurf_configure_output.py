#!/usr/bin/env python
# encoding: utf-8

# This tools overrides the output directory / build
# directory of waf. This is mainly to support cross-
# compilation into separated output directories.

import os

from waflib import Utils
from waflib import Context
from waflib import Options

from waflib.Configure import ConfigurationContext


class ToolchainConfigurationContext(ConfigurationContext):

    '''configures the project'''


    def init_dirs(self):
        # Waf calls this function to set the output directory.
        # Waf sets the output dir in the following order
        # 1) Check whether the -o option has been specified
        # 2) Check whether the wscript has an out variable defined
        # 3) Fall-back and use the name of the lock-file
        #
        # In order to not surprise anybody we will disallow the out variable
        # but allow our output dir to be overwritten by using the -o option

        assert(getattr(Context.g_module, Context.OUT, None) is None)

        if not Options.options.out:

            if self.has_tool_option('cxx_mkspec'):
                mkspec = self.get_tool_option('cxx_mkspec')
                self.out_dir = os.path.join("build", mkspec)
            else:
                build_platform = Utils.unversioned_sys_platform()
                self.out_dir = os.path.join("build", build_platform)

            # Use the _debug postfix for debug builds
            if self.has_tool_option('cxx_debug'):
                self.out_dir += '_debug'

        super(ToolchainConfigurationContext, self).init_dirs()
