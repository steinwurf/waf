#! /usr/bin/env python
# encoding: utf-8

from waflib import Context


class WafUpgradeContext(Context.Context):
    """upgrades the given dependencies, and the dependencies they pull in"""

    cmd = "upgrade"
    fun = "resolve"

    def execute(self):
        # The dependencies are upgraded in the resolve step, which the options
        # context runs before any command is executed
        pass


WafUpgradeContext.__doc__ = (
    "upgrades the given dependencies, and the dependencies they pull in"
)
