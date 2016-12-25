#!/usr/bin/env python
# encoding: utf-8

from waflib.Build import BuildContext

from . import wurf_resolve_context


class WurfBuildContext(BuildContext):


    def __init__(self, **kw):
        super(WurfBuildContext, self).__init__(**kw)

    def execute(self):

        super(WurfBuildContext, self).execute()

        # Call configure in all dependencies
        wurf_resolve_context.recurse_dependencies(self)
