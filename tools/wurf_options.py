#!/usr/bin/env python
# encoding: utf-8

"""
WurfOptions overrides waf's default OptionsContext if it is imported in the
top-level wscript of a project like this:

    import waflib.extras.wurf_options

The tool overrides the 'parse_args' function to allow the definition of
options in dependencies. The passed options are parsed twice. The first time
all options are allowed as it is not possible to validate options that are not
yet defined. The second parsing will happen after the dependencies are fully
resolved, and therefore all options are known.

The dependencies are resolved with the "resolve" context, which is created
and executed in parse_args. This is a simplified version of the configuration
context, and it follows the standard control flow. First, it will call the
"resolve" function in the top-level wscript of the project. In that function,
we load "wurf_common_tools" which in turn loads "wurf_dependency_bundle",
"wurf_dependency_resolve" and "wurf_git". These tools are used to download
the dependencies.

The project's top-level dependencies are defined in the wscript's "resolve"
function like this (after loading "wurf_common_tools"):

def resolve(ctx):
    import waflib.extras.wurf_dependency_resolve as resolve

    ctx.load('wurf_common_tools')

    ctx.add_dependency(resolve.ResolveVersion(
        name='waf-tools',
        git_repository='github.com/steinwurf/waf-tools.git',
        major=2))

When a dependency is added, wurf_dependency_bundle tries to resolve the
project. This only happens if this is an active resolve step, i.e. if
"configure" is given in the waf commands. In a passive resolve step, the
tool only enumerates the dependencies that the previously resolved
dependencies to fetch the options from these.

After downloading/resolving a dependency, we also recurse into the wscript
of that dependency where the "resolve" function adds the dependencies of
that project. These dependencies are resolved immediately in a recursive way.
A dependency can also define options in the "resolve" function by accessing
the original option parser using "ctx.opt":

def resolve(ctx):
    opts = ctx.opt.add_option_group('Makespec options')
    opts.add_option(
        '--cxx_mkspec', default=None, dest='cxx_mkspec',
        help="C++ make specification")
"""


import os
import sys
import copy

from waflib import Context
from waflib import Options


class WurfOptions(Options.OptionsContext):

    def parse_args(self):

        # First, we create a deep copy of the original parser of the
        # OptionsContext, because we will modify the options and arguments
        # of this copied parser, and these changes should not affect the
        # original parser
        extra_parser = copy.deepcopy(self.parser)

        # Get the option strings that were defined in waflib/Options.py or
        # in the options function of the top-level wscript.
        # These are the "pre-defined" options
        optstrings = \
            [x.get_opt_string() for x in extra_parser._get_all_options()]

        # Create a group for the extra options that were passed but are not
        # defined at this point, because they come from a yet-to-be-resolved
        # dependency. Essentially, we just make optparse eat any option
        # strings that start with "--"
        extra_opts = extra_parser.add_option_group('Extra options')

        # Go though the arguments that start with --
        for arg in sys.argv[1:]:
            if arg.startswith('--'):
                key = arg.split('=', 1)[0]
                # Ignore the pre-defined options
                if key not in optstrings:
                    # Handle key-value pairs and boolean options differently
                    if '=' in arg:
                        extra_opts.add_option(key, default=None,
                                              dest=key[2:])
                    else:
                        extra_opts.add_option(key, default=False,
                                              action='store_true',
                                              dest=key[2:])

        # Copy the arguments array. This copy might be modified if we have
        # to remove the help flags for the extra_parser.
        args = sys.argv[:]
        show_help = '-h' in sys.argv or '--help' in sys.argv

        # Note that parse_args will print the help text and exit the
        # application if the help flags are present. This would prevent us
        # from fetching options from dependencies during the resolve step.
        if show_help:
            if '-h' in args: args.remove('-h')
            if '--help' in args: args.remove('--help')

        # Call the extra_parser where the extra options are allowed and the
        # help flags are removed. Note that Options.options must be properly
        # initialized before we can create the resolve context.
        (Options.options, leftover_args) = extra_parser.parse_args(args)

        # Create and execute the resolve context
        ctx = Context.create_context('resolve')
        ctx.options = Options.options # provided for convenience
        ctx.cmd = 'resolve'
        # The original OptionsContext can be used to add options in the
        # resolve functions of the dependencies. These options will be handled
        # as normal options when we call parse_args on the original parser.
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

        # Call the parse_args of the super class to parse all the arguments
        # again after adding options from dependencies during the execution
        # of the resolve step. At this point, optparse will know about all
        # the supported options, so it can validate those.
        super(WurfOptions, self).parse_args()
