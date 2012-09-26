#!/usr/bin/env python
# encoding: utf-8

def configure(conf):
    """
    This is the default android toolchain. We use a single setup which we expect
    to work with all Android toolchains however in the future we might have to
    make the choice more specific i.e. android-x86 or similar.
    """
    conf.gxx_common_flags()
    conf.cxx_load_tools()

    # Setup compiler and linker
    conf.find_program('arm-linux-androideabi-g++', var='CXX')
    conf.env['LINK_CXX'] = conf.env['CXX']

    conf.find_program('arm-linux-androideabi-gcc', var='CC')

    #Setup archiver and archiver flags
    conf.find_program('arm-linux-androideabi-ar', var='AR')
    conf.env['ARFLAGS'] = "rcs"

    #Setup android asm
    conf.find_program('arm-linux-androideabi-as', var='AS')

    #Setup android nm
    conf.find_program('arm-linux-androideabi-nm', var='NM')

    #Setup android ld
    conf.find_program('arm-linux-androideabi-ld', var='LD')

    # Set the andoid define - some libraries rely on this define being present
    conf.env.DEFINES += ['ANDROID']

    conf.env['CXXFLAGS'] += [
                             '-O2',
                             '-g',
                             '-ftree-vectorize',
                             '-Wextra',
                             '-Wall',
                             '-std=gnu++0x',
                            ]
