#!/usr/bin/env python
# encoding: utf-8

import os
import sys
from waflib.Configure import conf
from waflib import Options


def _check_minimum_python_version(opt, major, minor):
    if sys.version_info[:2] < (major, minor):
        opt.fatal("Python version not supported: {0}, "
                  "required minimum version: {1}.{2}"
                  .format(sys.version_info[:3], major, minor))


def options(opt):
    # wurf_common_tools is loaded first in every project,
    # therefore it is a good entry point to check the minimum Python version
    _check_minimum_python_version(opt, 2, 7)

    opt.load('wurf_resolve_context')
    opt.load('wurf_configure_output')
    opt.load('wurf_dependency_bundle')
    opt.load('wurf_standalone')


def resolve(ctx):
    # Only run the resolve step from the top-level wscript
    if ctx.is_toplevel():
        ctx.load('wurf_dependency_bundle')


def configure(conf):
    # Only run the configure step from the top-level wscript
    if conf.is_toplevel():
        # Store the options that are specified during the configure step
        conf.env["stored_options"] = Options.options.__dict__.copy()

        conf.load('wurf_dependency_bundle')


def build(bld):
    # Only run the build step from the top-level wscript
    if bld.is_toplevel():
        bld.load('wurf_dependency_bundle')


@conf
def is_toplevel(self):
    """
    Returns true if the current script is the top-level wscript
    """
    return self.srcnode == self.path


@conf
def get_tool_option(conf, option):
    # Options can be specified in 2 ways:
    # 1) Passed with the currently executed command
    # 2) Stored during the configure step
    current = Options.options.__dict__
    stored = conf.env.stored_options

    if option in current:
        return current[option]
    elif option in stored:
        return stored[option]
    else:
        conf.fatal('Missing option: %s' % option)


@conf
def has_tool_option(conf, option):
    current = Options.options.__dict__
    stored = conf.env.stored_options

    if option in current:
        return (current[option] != None)
    elif option in stored:
        return (stored[option] != None)
    else:
        return False
