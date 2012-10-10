#! /usr/bin/env python
# encoding: utf-8
# Matt Clarkson, 2012


import platform, os
from waflib.TaskGen import extension
from waflib.Configure import conf

def options(opt):
    opt.load('wurf_protoc')

def configure(conf):
    conf.load('wurf_protoc')

@conf
def protobuf_disable_warnings(conf):

    # Disable warnings as the protobuf headers have problems (well Microsoft
    # thinks they have problems).  See the vsprojects\readme.txt for
    # information in the Google Protocol Buffers release

    if conf.env.CXX_NAME == 'msvc':
        # conversion from 'type1' to 'type2', possible loss of data
        # http://msdn.microsoft.com/en-us/library/3hca13eh
        self.env.append_unique('CXXFLAGS', ['/wd4242'])
        # conversion from 'type1' to 'type2', possible loss of data
        # http://msdn.microsoft.com/en-us/library/2d7604yb
        self.env.append_unique('CXXFLAGS', ['/wd4244'])
        # conversion from 'type_1' to 'type_2', signed/unsigned mismatch
        # http://msdn.microsoft.com/en-us/library/ms173683
        self.env.append_unique('CXXFLAGS', ['/wd4365'])
        # conversion from 'size_t' to 'type', possible loss of data
        # http://msdn.microsoft.com/en-us/library/6kck0s93
        self.env.append_unique('CXXFLAGS', ['/wd4267'])
        # copy constructor could not be generated because a base class copy
        # constructor is inaccessible
        # http://msdn.microsoft.com/en-us/library/306zwa5e
        self.env.append_unique('CXXFLAGS', ['/wd4625'])
        # assignment operator could not be generated because a base class
        # assignment operator is inaccessible
        # http://msdn.microsoft.com/en-US/library/6ay4xcyd
        self.env.append_unique('CXXFLAGS', ['/wd4626'])


@extension('.proto')
def process_protoc(self, node):
    task = self.create_task('protoc', node)
    cpp_node = node.change_ext('.pb.cc')
    hpp_node = node.change_ext('.pb.h')
    out_node = hpp_node.parent
    task.set_outputs([cpp_node, hpp_node])
    task.flags = [
        '--cpp_out=%s' % out_node.abspath(),
        '-I%s' % node.parent.abspath()
    ]
    self.env.append_unique('INCLUDES', [out_node])
    if 'PROTOBUF' not in getattr(self, 'use', []):
        self.use = self.to_list(getattr(self, 'use', '')) + ['PROTOBUF']
    # Add some methods that are required for compiling the resulting C++ file
    # if the C++ feature is not added
    for meth in ['apply_incpaths']:
        if meth not in self.meths:
            self.meths.append(meth)
    self.get_hook(cpp_node)(self, cpp_node)

