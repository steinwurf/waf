#!/usr/bin/env python
# encoding: utf-8

import os

def options(opt):
    
    toolchain_opts = opt.add_option_group('mkspecs')

    toolchain_opts.add_option(
        '--cxx-mkspec', default = None,
        dest='cxx_mkspec',
        help="Select a specific cxx_mkspec. "+
             "Example: --cxx_mkspec=cxx_gxx46_arm_android")

    toolchain_opts.add_option(
        '--cxx-mkspec-options', default = None, action="append",
        dest='cxx_mkspec_options',
        help="Some mkspec requires additional options, you can this option "
             "multiple times. Example use: --cxx-mkspec-options="
             "NDK_DIR=~/.android-standalone-ndk/gcc4.6/bin")

    opt.load("compiler_cxx")


def configure(conf):

    if not conf.has_dependency_path('waf-tools'):
        conf.fatal('The wurf_cxx_mkspec tools require the external-waf-tools'
                   ' repository to be added as dependency')

    # Get the path and load the tool
    path = conf.dependency_path('waf-tools')

    conf.load('wurf_cxx_mkspec_tool', os.path.join(path, 'mkspec')) 

