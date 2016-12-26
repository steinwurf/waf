#!/usr/bin/env python
# encoding: utf-8

from waflib.Build import BuildContext

from . import wurf_resolve_context


class WurfBuildContext(BuildContext):


    def __init__(self, **kw):
        super(WurfBuildContext, self).__init__(**kw)

    def execute(self):
     
        print("IN BUILDDDDDDDDDDD")
        super(WurfBuildContext, self).execute()


    def recurse(self, dirs, name=None, mandatory=True, once=True, encoding=None):
        
        print("HOHOHOHOHOHOHOH")
        self.to_log("wurf: Recurse {}".format(dirs))
        
        super(WurfBuildContext, self).recurse(dirs=dirs, name=name, 
            mandatory=mandatory, once=once, encoding=encoding)
            
    # Call build in all dependencies
    #wurf_resolve_context.recurse_dependencies(self)
    
    def pre_build(self):
        #wurf_resolve_context.recurse_dependencies(self)
            
        super(WurfBuildContext, self).pre_build()
