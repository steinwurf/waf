#!/usr/bin/env python
# encoding: utf-8

from waflib.Build import BuildContext

# TEMP
import waflib.Logs
import os

from . import wurf_resolve_context


class WurfBuildContext(BuildContext):


    def __init__(self, **kw):
        super(WurfBuildContext, self).__init__(**kw)
        
    def to_log(self, msg):
        print(msg)
    
    def execute(self):
     
        self.to_log("wurf: WurfBuildContext execute\n")
        super(WurfBuildContext, self).execute()

    def pre_recurse(self, node):
        self.to_log("wurf: pre_recurse {}".format(node))
        super(WurfBuildContext, self).pre_recurse(node)

    def recurse(self, dirs, name=None, mandatory=True, once=True, encoding=None):
            
        self.to_log("wurf: WurfBuildContext recurse {}\n".format(dirs))
        
        super(WurfBuildContext, self).recurse(dirs=dirs, name=name, 
            mandatory=mandatory, once=once, encoding=encoding)
                
    def pre_build(self):
        self.to_log("wurf: WurfBuildContext pre_build\n")

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
        wurf_resolve_context.recurse_dependencies(self)
        super(WurfBuildContext, self).pre_build()
