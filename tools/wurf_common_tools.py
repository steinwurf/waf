#!/usr/bin/env python
# encoding: utf-8


def options(opt):

    opt.load('wurf_tools')
    opt.load('wurf_configure_output')
    opt.load('wurf_dependency_bundle')
    opt.load('wurf_standalone')


def configure(conf):

    # wurf_tools must be loaded before waf-tools is resolved and recursed by
    # wurf_dependency_bundle, because the external tools will need the
    # tool options that are parsed when wurf_tools is configured
    conf.load('wurf_tools')
    conf.load('wurf_dependency_bundle')

def build(bld):

    bld.load('wurf_dependency_bundle')
