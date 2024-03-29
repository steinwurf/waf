#!/usr/bin/env python
# encoding: utf-8

import os
import sys

from waflib import Context
from waflib import Options
from waflib import Logs


from . import registry
from . import waf_conf


class WafOptionsContext(Options.OptionsContext):
    """Custom options context which will initiate the dependency resolve step.

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

        # Create option group for resolve options.
        self.resolve_options_group = self.add_option_group("Resolve options")

        # Add option to skip resolve
        self.resolve_options_group.add_option(
            "--no_resolve", default=False, action="store_true"
        )

        # Add option to skip internal dependencies
        self.resolve_options_group.add_option(
            "--skip_internal", default=False, action="store_true"
        )

    def execute(self):

        self.srcnode = self.path

        # Build the registry
        self.registry = registry.options_registry(ctx=self, git_binary="git")

        # To avoid logs going to stdout create an logger
        bldnode = self.path.make_node("build")
        bldnode.mkdir()

        log_path = os.path.join(bldnode.abspath(), "options.log")

        self.logger = Logs.make_logger(path=log_path, name="options")
        self.logger.debug("wurf: Options execute")

        # Peek into the options and see of --no_resolve was passed
        # if it was skip the resolve. We have at this point not parsed
        # the options so we just do it manually
        resolve = "--no_resolve" not in sys.argv

        # Peek into the options and see of --skip_internal was passed
        # if it was skip the internal dependencies.
        skip_internal = "--skip_internal" in sys.argv

        # Create and execute the resolve context
        ctx = Context.create_context(
            "resolve", resolve=resolve, skip_internal=skip_internal
        )

        try:
            ctx.execute()
        finally:
            ctx.finalize()

        # Fetch the resolve options parser such that we can
        # print help if needed:
        if resolve:
            self.wurf_options = ctx.registry.require("options")

            # Fetch the arguments not parsed in the resolve step
            # We are just interested in the left-over args, which is the
            # second value returned by parse_known_args(...)
            self.waf_options = self.wurf_options.unknown_args
        else:
            self.waf_options = sys.argv

        # Load any extra tools that define regular options for waf
        self.load("wurf.waf_standalone_context")

        # Call options() in all dependencies: all options must be defined
        # before running OptionsContext.execute() where parse_args is called
        waf_conf.recurse_dependencies(self)

        # This caused some issues on windows since we make a logger to
        # intercept calls being run during options(). If we keep this
        # logger around while calling super(WafOptionsContext, self).execute()
        # some process are being allocated. These process will inherit the
        # open file descriptors - meaning we cannot remove the log file
        # in e.g. a subsequent call to waf clean.
        handlers = self.logger.handlers[:]
        for handler in handlers:
            handler.close()
            self.logger.removeHandler(handler)

        super(WafOptionsContext, self).execute()

    def is_toplevel(self):
        """
        Returns true if the current script is the top-level wscript
        """
        return self.srcnode == self.path

    def parse_args(self, _args=None):
        """Override the parse_args(..) from the OptionsContext.

        Here we inject the arguments which were not consumed in the resolve
        step.
        """
        # We expect _args to be None here, if it isn't we should probably
        # figure out why and see if we should combine it with the
        # self.waf_options list
        assert _args is None

        try:
            # We may not have a wurf_options instance if running in a folder
            # without a wscript (see class documentation)
            # If the instance is present, we copy all the resolve options
            # from the argparse.ArgumentParser to optparse.OptionParser that
            # was created by waf. This way, optparse can print out a unified
            # help text and option errors will be printed as the last line.
            if self.wurf_options:
                # argparse.ArgumentParser groups all optional arguments to
                # the "_optionals" groups by default
                source_group = self.wurf_options.parser._optionals

                for action in source_group._group_actions:
                    self.resolve_options_group.add_option(
                        action.option_strings[0],
                        action="store_true" if action.nargs == 0 else "store",
                        help=action.help,
                    )
        finally:
            super(WafOptionsContext, self).parse_args(_args=self.waf_options)
