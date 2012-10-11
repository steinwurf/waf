#!/usr/bin/env python
# encoding: utf-8

import os, sys

from waflib import Utils
from waflib import Context
from waflib import Options

import importlib

def options(opt):
    toolchain_opts = opt.add_option_group('MKSpecs')

    platform = Utils.unversioned_sys_platform()

    default_value = ""

    if platform == "linux":
        default_value = "cxx_%s_gxx" % platform
    elif platform == "win32":
        default_value = "cxx_%s_msvc" % platform
    elif platform == "darwin":
        default_value = "cxx_%s_macports" % platform

    toolchain_opts.add_option('--cxx_mkspec', default = default_value,
                              dest='cxx_mkspec',
                              help="Select a specific cxx_mkspec "
                                   "[default: %default]"
                                   ", other example --cxx_mkspec=cxx_android_gxx")

    toolchain_opts.add_option('--cxx_mkspec-path', default=None,
                              dest='cxx_mkspec_path',
                              help='Set the path to the cxx_mkspec')

def configure(conf):
    # Check to see if we should look for the mkspec in another path
    cxx_mkspec_path = getattr(conf.options, 'cxx_mkspec_path', None)

    cxx_mkspec = getattr(conf.options, 'cxx_mkspec', '')

    if cxx_mkspec_path:
        cxx_mkspec_path = os.path.expanduser(cxx_mkspec_path)
        cxx_mkspec_path = os.path.abspath(cxx_mkspec_path)

        conf.msg('Setting cxx_mkspec path to:', cxx_mkspec_path)

        conf.load(cxx_mkspec, cxx_mkspec_path)

    else:
        conf.load(cxx_mkspec)
