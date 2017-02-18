#!/usr/bin/env python
# encoding: utf-8

from waflib.Build import BuildContext


class WafBuildContext(BuildContext):

    def pre_build(self):
        # Call build in all dependencies.
        #
        # Note, why is this placed here? The BuildContext in waf will call this
        # function right after recursing into the main wscript. The purpose of
        # it seems to be to allow the user to hook up some user-defined functions
        # right before starting a build.
        #
        # https://github.com/waf-project/waf/blob/master/waflib/Build.py#L269
        #
        #  Which is more or less what we want to do. Here we recurse into to the
        #  dependencies build functions allowing them to also hook up
        #  user-defined build functions.
        self.recurse_dependencies()
        super(WafBuildContext, self).pre_build()
