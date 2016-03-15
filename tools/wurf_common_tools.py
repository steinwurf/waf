#!/usr/bin/env python
# encoding: utf-8

import os
import sys
from waflib.Configure import conf
from waflib import Options




def options(opt):


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

    if option in current and current[option] != None:
        return current[option]
    elif option in stored and stored[option] != None:
        return stored[option]
    else:
        conf.fatal('Missing option: %s' % option)


@conf
def has_tool_option(conf, option):
    current = Options.options.__dict__
    stored = conf.env.stored_options

    if option in current and current[option] != None:
        return True
    elif option in stored and stored[option] != None:
        return True
    else:
        return False
