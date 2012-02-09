#!/usr/bin/env python
# encoding: utf-8

import os

from waflib import Utils

def options(opt):
    toolchain_opts = opt.add_option_group('Toolchain')

    toolchain_opts.add_option('--toolchain', default=Utils.unversioned_sys_platform(),
                              dest='toolchain',
                              help="Select a specific toolchain [default: %default]"
                                   ", other example --toolchain=android.")

    toolchain_opts.add_option('--toolchain-path', default=None, dest='toolchain_path',
                              help='Set the path to the toolchain')
    
    opt.load('compiler_cxx')



def platform_toolchain(conf):
    """
    We just select the platform default toolchain. And rely on Waf to detect it
    """
    
    conf.load('compiler_cxx')


def android_toolchain(conf):
    """
    We wish to use the Android toolchain atm. we use a single setup which we expect
    to work with all Android toolchains however in the future we might have to
    make the choice more specific i.e. android-x86 or similar.
    """
    conf.gxx_common_flags()
    conf.cxx_load_tools()

    if 'TOOLCHAIN_PATH' not in conf.env:
        conf.fatal('android toolchain requires a toolchain path')

    toolchain_dir = conf.env['TOOLCHAIN_PATH']

    toolchain_bin = os.path.join(toolchain_dir, 'bin')

    paths = [toolchain_bin]
    
    # Setup compiler and linker
    conf.find_program('arm-linux-androideabi-g++', path_list=paths, var='CXX')
    conf.env['LINK_CXX'] = conf.env['CXX']
    
    conf.find_program('arm-linux-androideabi-gcc', path_list=paths, var='CC')
    
    #Setup archiver and archiver flags
    conf.find_program('arm-linux-androideabi-ar', path_list=paths, var='AR')
    conf.env['ARFLAGS'] = "rcs"
    
    conf.env['BINDIR'] = os.path.join(toolchain_dir, 'arm-linux-androideabi/bin')
    
    # Set the andoid define - some libraries rely on this define being present
    conf.env.DEFINES += ['ANDROID']

    

def configure(conf):

    # Setup the toolchain configure functions
    t = dict()
    platform = Utils.unversioned_sys_platform()
    t[platform] = platform_toolchain
    t['android'] = android_toolchain

    # Check if a specific toolchain should be used
    toolchain = getattr(conf.options, 'toolchain', '')

    # Check if we support the toolchain (empty means default)
    if toolchain not in t:
        conf.fatal('The selected toolchain "%s" is not supported' % toolchain)        

    # Store in env
    conf.env['TOOLCHAIN'] = toolchain

    # Check if a specific toolchain should be used
    toolchain_path = getattr(conf.options, 'toolchain_path', None)

    if toolchain_path:
        toolchain_path = os.path.expanduser(toolchain_path)
        toolchain_path = os.path.abspath(toolchain_path)

        conf.msg('Setting toolchain path to:', toolchain_path)

        conf.env['TOOLCHAIN_PATH'] = toolchain_path
    
    # Get configure function for this toolchain
    function = t[toolchain]

    # Configure
    function(conf)
        
