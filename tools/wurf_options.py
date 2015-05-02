#!/usr/bin/env python
# encoding: utf-8

import os
import sys
import copy

from waflib import Context
from waflib import Options


class WurfOptions(Options.OptionsContext):

    def parse_args(self):

        # Copy the existing parser
        extra_parser = copy.deepcopy(self.parser)

        # Get the option strings that were already in waflib/Options.py or
        # in the options function of the top-level wscript
        optstrings = \
            [x.get_opt_string() for x in extra_parser._get_all_options()]

        # Create a group for the extra options that are not defined explicitly
        extra_opts = extra_parser.add_option_group('Extra options')

        # Go though the arguments that start with --
        for arg in sys.argv[1:]:
            if arg.startswith('--'):
                key = arg.split('=', 1)[0]
                # Skip the options that are already defined
                if key not in optstrings:
                    # Handle key-value pairs and boolean options
                    if '=' in arg:
                        extra_opts.add_option(key, default=None, dest=key[2:])
                    else:
                        extra_opts.add_option(key, default=False,
                                              action='store_true', dest=key[2:])


        args = sys.argv[:]
        show_help = '-h' in sys.argv or '--help' in sys.argv

        # Call our own parser where the extra options are allowed and the
        # help flags are removed. Options.options must be properly
        # initialized before we can create the resolve context.
        if show_help:
            if '-h' in args: args.remove('-h')
            if '--help' in args: args.remove('--help')

        (Options.options, leftover_args) = extra_parser.parse_args(args)

        # Create and execute the resolve context
        ctx = Context.create_context('resolve')
        ctx.options = Options.options # provided for convenience
        ctx.cmd = 'resolve'
        ctx.opt = self
        # If active_resolvers is true, then the dependency resolvers are
        # allowed to download the dependencies. If it is false, then the
        # dependency bundle will only recurse into the previously resolved
        # dependencies to fetch the options from these.
        ctx.active_resolvers = 'configure' in sys.argv and not show_help
        try:
            ctx.execute()
        finally:
            ctx.finalize()

        # Call the super after adding options from dependencies during the
        # execution of the resolve step
        super(WurfOptions, self).parse_args()
