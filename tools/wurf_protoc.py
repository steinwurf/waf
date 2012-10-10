#! /usr/bin/env python
# encoding: utf-8
# Philipp Bender, 2012
# Matt Clarkson, 2012

"""
A simple tool to integrate protocol buffers into your build system.

    def configure(conf):
        conf.load('compiler_cxx cxx protoc_cxx')

    def build(bld):
        bld.program(source = "main.cpp file1.proto proto/file2.proto",
                    target = "executable")

"""

import platform, os
from waflib.TaskGen import extension
from waflib.Configure import conf
from waflib import Task, Utils

def configure(conf):
    # Get the compiler
    conf.find_program('protoc', var='PROTOC')
    conf.env['PROTOC_ST'] = '-I%s'


@conf
def check_protobuf(conf):
    # We'll need the library too
    conf.check_cfg(package="protobuf", uselib_store="PROTOBUF",
            args=['--cflags', '--libs'])


class protoc(Task.Task):
    color = 'BLUE'
    ext_out = ['.h', 'pb.cc']

    def run(self):
        bld = self.generator.bld
        cmd = Utils.subst_vars('${PROTOC} ${PROTOC_FLAGS} ' +
                               '${PROTOC_ST:INCPATHS}', self.env).split()
        cmd.extend([a.abspath() for a in self.inputs])
        cmd.extend(self.flags)
        return self.exec_command(cmd)
