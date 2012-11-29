#!/usr/bin/env python
# encoding: utf-8

import os
from waflib.Configure import conf

def options(opt):
    
    tool_opts = opt.add_option_group('external tools')

    tool_opts.add_option(
        '--options', default = None, action="append",
        dest='tool_options',
        help="Some external Waf tools requires additional options, you can this option "
             "multiple times. Example use: --options="
             "NDK_DIR=~/.android-standalone-ndk/gcc4.6/bin. See more information about "
             "the external tool options here: http:/sdkfjdsl")


def read_tool_options(conf):
    conf.env["tool_options"] = {}
    if conf.options.tool_options:
        for options in conf.options.tool_options:
            for option in options.split(','):
                try:
                    key, value = option.split('=')
                except Exception, e:
                    conf.fatal("tool-options has to have the format"
                               "'KEY=VALUE', you specified %r, which resulted in"
                               "Error:'%s'" % (option, e))
                conf.env["tool_options"][key] = value

def configure(conf):
    read_tool_options(conf)

@conf
def get_tool_option(conf, option):
    if not option in conf.env['tool_options']:
        conf.fatal('No tool option %s, you can specify tool options as: '
                   './waf configure --options=KEY=VALUE')
    else:
        return conf.env['tool_options'][option]

@conf
def has_tool_option(conf, option):
    return option in conf.env['tool_options']

@conf
def load_external_tool(conf, category, name):

    if not conf.has_dependency_path('waf-tools'):
        conf.fatal('The external tools require the external-waf-tools'
                   ' repository to be added as dependency')

    # Get the path and load the tool
    path = conf.dependency_path('waf-tools')

    conf.load(name, os.path.join(path, category)) 


