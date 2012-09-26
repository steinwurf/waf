#!/usr/bin/env python
# encoding: utf-8

"""
Detect and setup the g++ compiler
"""

def configure(conf):
    """
    Configuration for g++
    """
    conf.load('gxx')
    conf.env['CXXFLAGS'] += [
                             '-O2',
                             '-g',
                             '-ftree-vectorize',
                             '-Wextra',
                             '-Wall',
                             '-std=c++0x',
                            ]