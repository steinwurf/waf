#!/usr/bin/env python
# encoding: utf-8

import os
from waflib.Configure import conf

def options(opt):
    tool_opts = opt.add_option_group('external tools')

    tool_opts.add_option(
        '--options', default = None, action="append",
        dest='tool_options',
        help="Some external Waf tools requires additional options, you can "
             "this option multiple times. See more information about the "
             "external tool options here: http:/sdkfjdsl")


def parse_options(options_string):
    result = {}
    if options_string:
        for options in options_string:
            for option in options.split(','):
                try:
                    key, value = option.split('=')
                    result[key] = value
                except ValueError, e:
                    result[option] = True
    return result

def _read_tool_options(conf):
    conf.env["tool_options"] = parse_options(conf.options.tool_options)


def configure(conf):
    _read_tool_options(conf)

def check_for_duplicate(conf):
    options = parse_options(conf.options.tool_options)
    for option in options:
        if (option in conf.env['tool_options'] and
            conf.env['tool_options'][option] != options[option]):
            conf.fatal("Redefined option '%s' from %s to '%s', "
                       "re-run configure, to override the old value."
                       % (option,
                          conf.env['tool_options'][option],
                          options[option]))

@conf
def get_tool_option(conf, option):
    check_for_duplicate(conf)
    value = None
    if option in conf.env.tool_options:
        value = conf.env.tool_options[option]
    elif option in conf.options.tool_options:
        value = conf.options.tool_options[option]
    else:
        conf.fatal('No tool option %s, you can specify tool options as: '
                   './waf configure --options=KEY=VALUE' % option)
    return value

@conf
def has_tool_option(conf, option):
    check_for_duplicate(conf)
    return option in conf.env.tool_options or option in parse_options(conf.options.tool_options)

@conf
def load_external_tool(conf, category, name):

    if not conf.has_dependency_path('waf-tools'):
        conf.fatal('The external tools require the external-waf-tools'
                   ' repository to be added as dependency')

    # Get the path and load the tool
    path = conf.dependency_path('waf-tools')

    conf.load(name, os.path.join(path, category))

