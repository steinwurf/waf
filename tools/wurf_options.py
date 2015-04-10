#!/usr/bin/env python
# encoding: utf-8

import os
import sys

from waflib import Utils
from waflib import Context
from waflib import Options


class WurfOptions(Options.OptionsContext):

    def parse_args(self):

        # Get the defined option strings (e.g. '--jobs1', '--help')
        optstrings = \
            [x.get_opt_string() for x in self.parser._get_all_options()]

        # Create a group for the extra options that are not defined explicitly
        extra_opts = self.add_option_group('Extra options')

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

        # Call the super after the extra options are added
        super(WurfOptions, self).parse_args()
