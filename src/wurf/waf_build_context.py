#!/usr/bin/env python
# encoding: utf-8

from waflib.Build import BuildContext


class WafBuildContext(BuildContext):

    def execute_build(self):

        # Call build() in all dependencies before executing build()
        # in the top-level wscript: this allows us to define all build tasks
        # from the dependencies before reaching the main project
        self.recurse_dependencies()

        super(WafBuildContext, self).execute_build()
