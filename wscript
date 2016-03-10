#! /usr/bin/env python
# encoding: utf-8

import os

from waflib import Build

top = '.'

def resolve(ctx):
    pass

def configure(conf):

    # Ensure that the waf-light program is available in the in the
    # third_party/waf folder. This is used to build the waf binary.
    conf.find_program('waf-light', path_list=['third_party/waf'])

    # Make sure we tox used for running unit tests
    conf.find_program('tox')

def build(bld):

    # Waf checks that source files are available when we create the
    # different tasks. We can ask waf to lazily do this because the waf
    # binary is not created until after we run the waf-light build
    # step. This is manipulated using the post_mode.
    bld.post_mode = Build.POST_LAZY

    # Invoke tox to run all the pure Python unit tests
    bld(rule='tox')

    bld.add_group()

    # We need to invoke the waf-light from within the third_party/waf
    # folder as waf-light will look for wscript in the folder where the
    # executable was started - so we need to start it from the right
    # folder. Using cwd we can make sure the python process is lauched in
    # the right directory.
    bld(rule='python waf-light --make-waf', cwd='third_party/waf')

    bld.add_group()

    # Copy the waf binary to build directory
    bld(features='subst',
        source='third_party/waf/waf',
        target=bld.bldnode.make_node('waf'),
        is_copy=True)
