#!/usr/bin/env python
# encoding: utf-8

def configure(conf):
    """
    We just select the platform default toolchain. And rely on Waf to detect it
    """

    conf.load('compiler_cxx')
    ['/O2', '/Ob2', '/W3', '/MT', '/EHs']