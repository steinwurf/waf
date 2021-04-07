#! /usr/bin/env python
# encoding: utf-8

# Support for python 2
try:
    import configparser
except ImportError:
    import ConfigParser as configparser

import os


CONFIG_FILE = os.path.expanduser('~/.wurf_config')


class ConfigFile(object):

    def __init__(self, ctx):
        
        self.default_resolve_path = None
        self.default_symlinks_path = None
        self.ctx = ctx
        if not os.path.isfile(CONFIG_FILE):
            return
        
        self.ctx.start_msg("Using config file")
        config = configparser.ConfigParser()
        try:
            config.read(CONFIG_FILE)
        except configparser.Error as e:
            self.ctx.end_msg("ERROR: " + e.message, color='RED')
            return

        self.ctx.end_msg(CONFIG_FILE)
        if config.has_option('DEFAULT', 'resolve_path'):
            self.default_resolve_path = config.get('DEFAULT', 'resolve_path')
            self.ctx.msg("resolve_path", self.default_resolve_path)

        if config.has_option('DEFAULT', 'symlinks_path'):
            self.default_symlinks_path = config.get('DEFAULT', 'symlinks_path')
            self.ctx.msg("symlinks_path", self.default_symlinks_path)
