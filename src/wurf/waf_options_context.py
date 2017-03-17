#!/usr/bin/env python
# encoding: utf-8

"""
WurfOptions overrides waf's default OptionsContext if it is imported in the
top-level wscript of a project like this:

    import waflib.extras.wurf_options

This step can be done automatically by building a custom waf binary and
using the --prelude statement (see more here http://bit.ly/1Te4mRz).

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
tool only enumerates the  previously resolved dependencies to fetch the
options from these.

After downloading/resolving a dependency, we also recurse into the wscript
of that dependency where the "resolve" function adds the dependencies of
that project. These dependencies are resolved immediately in a recursive way.
A dependency can also define options in the "resolve" function by accessing
the original option parser using "ctx.opt":

def resolve(ctx):
    opts = ctx.opt.add_option_group('Makespec options')
    opts.add_option('--cxx_mkspec', default=None, dest='cxx_mkspec',
                    help="C++ make specification")
"""


import os
import sys
import copy

from waflib import Context
from waflib import Options

from . import waf_conf

class WafOptionsContext(Options.OptionsContext):
    """ Custom options context which will initiate the dependency resolve step.

    Default waf will instantiate and use this context in two different ways:

    1. If waf is executed in a folder without a wscript, waf will simply create
       the context and then directly call parse_args(...) without running
       execute(...). This can be seen in:
       https://github.com/waf-project/waf/blob/master/waflib/Scripting.py#L130-L139

    2. Standard, where the options context is instantiated and executed:
       https://github.com/waf-project/waf/blob/master/waflib/Scripting.py#L262
    """

    def __init__(self, **kw):
        super(WafOptionsContext, self).__init__(**kw)

        # List containing the command-line arguments not parsed
        # by the resolve context options parser. These are the
        # arguments that waf's defalt options parser
        self.waf_options = None

        # Options parser used in the resolve step.
        self.wurf_options = None

    def execute(self):

        self.srcnode = self.path

        # Create and execute the resolve context
        ctx = Context.create_context('resolve')

        try:
            ctx.execute()
        finally:
            ctx.finalize()

        # Fetch the resolve options parser such that we can
        # print help if needed:
        self.wurf_options = ctx.registry.require('options')

        # Fetch the arguments not parsed in the resolve step
        # We are just interested in the left-over args, which is the
        # second value retuned by parse_known_args(...)
        self.waf_options = self.wurf_options.unknown_args

        # Call options() in all dependencies: all options must be defined
        # before running OptionsContext.execute() where parse_args is called
        waf_conf.recurse_dependencies(self)

        super(WafOptionsContext, self).execute()

    def is_toplevel(self):
        """
        Returns true if the current script is the top-level wscript
        """
        return self.srcnode == self.path

    def parse_args(self, _args=None):
        """ Override the parse_args(..) from the OptionsContext.

        Here we inject the arguments which were not consumed in the resolve
        step.
        """

        # We expect _args to be None here, if it isn't we should probably
        # figure out why and see if we should combine it with the
        # self.waf_options list
        assert(_args is None)

        try:
            super(WafOptionsContext, self).parse_args(_args=self.waf_options)

        except SystemExit:

            # If optparse (which is the options parser use by waf) sees
            # -h or --help it will call sys.exit(0) to stop the program and
            # print the help message for the user.
            #
            # sys.exit() will raise the SytemExit exception so an easy way for
            # us to add our help message here is to catch that and print our
            # help and then re-raise.

            if self.wurf_options:
                # We may not have a wurf_parser if running in a folder
                # without a wscript (see class documentation)
                self.wurf_options.parser.print_help()

            raise
