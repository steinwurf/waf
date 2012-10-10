#!/usr/bin/env python
# encoding: utf-8

from waflib.Tools import gxx

"""
Detect and setup the clang compiler
"""

def configure(conf):
    """
    Configuration for clang++
    """
    
    clang = conf.find_program('clang++', var='CXX')
    
@conf
def configure_clang(conf):   
    clang = conf.cmd_to_list(conf.env.CXX)
    conf.get_cc_version(clang, gcc=True)
    conf.env.CXX_NAME = 'clang'
    conf.env.CXX      = clang

    print conf.env['CC_VERSION']

    conf.find_ar()
    conf.gxx_common_flags()
    conf.gxx_modifier_platform()
    conf.cxx_load_tools()
    conf.cxx_add_flags()
    conf.link_add_flags()
    
    conf.env['LINK_CXX'] = conf.env['CXX']
    
    conf.env['CXXFLAGS'] += [
                            '-O2',
                            '-g',
                            '-Wextra',
                            '-Wall',
                            '-std=c++0x',
                            ]