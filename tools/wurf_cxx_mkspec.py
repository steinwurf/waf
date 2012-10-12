#!/usr/bin/env python
# encoding: utf-8

import os, sys

from waflib import Utils
from waflib import Context
from waflib import Options

from waflib.Configure import conf
from waflib.Configure import ConfigurationContext

###############################
# ToolchainConfigurationContext
###############################

class ToolchainConfigurationContext(ConfigurationContext):
    '''configures the project'''
    cmd='configure'

    def init_dirs(self):
        # Waf calls this function to set the output dir.
        # Waf sets the output dir in the following order
        # 1) Check whether the -o option has been specified
        # 2) Check whether the wscript has an out varialble defined
        # 3) Fallback and use the name of the lockfile
        #
        # In order to not suprise anybody we will disallow the out variable
        # but allow our output dir to be overwritten by using the -o option

        assert(getattr(Context.g_module,Context.OUT,None) == None)

        if not Options.options.out:
            if Options.options.cxx_mkspec:
                self.out_dir = "build/"+Options.options.cxx_mkspec
            else:
                build_platform = Utils.unversioned_sys_platform()
                self.out_dir = "build/" + build_platform

        super(ToolchainConfigurationContext, self).init_dirs()



def options(opt):
    toolchain_opts = opt.add_option_group('mkspecs')

    toolchain_opts.add_option('--cxx_mkspec', default = None,
                              dest='cxx_mkspec',
                              help="Select a specific cxx_mkspec "
                                   "[default: %default]"
                                   ", other example --cxx_mkspec=cxx_android_gxx")
    opt.load("compiler_cxx")

def configure(conf):
    # Check to see if we should look for the mkspec in another path

    mkspec = "cxx_default"

    if conf.options.cxx_mkspec:
        mkspec = conf.options.cxx_mkspec

    cxx_mkspec_path = conf.env["BUNDLE_DEPENDENCIES"]["mkspec"]
    conf.msg('Setting cxx_mkspec path to:', cxx_mkspec_path)
    conf.load(mkspec, cxx_mkspec_path)
