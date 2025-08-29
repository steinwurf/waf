#!/usr/bin/env python
# encoding: utf-8

from waflib.Build import InstallContext


class WafInstallContext(InstallContext):
    def pre_recurse(self, node):

        super(WafInstallContext, self).pre_recurse(node)

        # Call build() in all dependencies before executing build()
        # in the top-level wscript: this allows us to define all build tasks
        # from the dependencies before reaching the main project
        # if self.is_toplevel():
        #     self.recurse_dependencies()
