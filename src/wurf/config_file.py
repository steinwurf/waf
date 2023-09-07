#! /usr/bin/env python
# encoding: utf-8

import configparser
import os

LOCAL_CONFIG_FILE = os.path.abspath(".wurf_config")
USER_CONFIG_FILE = os.path.abspath(os.path.expanduser("~/.wurf_config"))


class ConfigFile(object):
    def __init__(self, ctx):
        self.default_resolve_path = None
        self.ctx = ctx
        if os.path.isfile(LOCAL_CONFIG_FILE):
            config_file = LOCAL_CONFIG_FILE
        elif os.path.isfile(USER_CONFIG_FILE):
            config_file = USER_CONFIG_FILE
        else:
            # No config file found
            return

        # Only write to the log if the context has a logger set.
        log = self.ctx.logger is not None

        if log:
            self.ctx.start_msg("Using config file")
        config = configparser.ConfigParser()
        try:
            config.read(config_file)
        except configparser.Error as e:
            if log:
                self.ctx.end_msg("ERROR: " + e.message, color="RED")
            return

        if log:
            self.ctx.end_msg(config_file)

        if config.has_option("DEFAULT", "resolve_path"):
            self.default_resolve_path = config.get("DEFAULT", "resolve_path")

            if log:
                self.ctx.msg("Default resolve path", self.default_resolve_path)
