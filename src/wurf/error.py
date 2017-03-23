#! /usr/bin/env python
# encoding: utf-8

class Error(Exception):
    """Basic exception for errors raised by wurf tools"""
    def __init__(self, msg):
        super(Error, self).__init__(msg)

class CmdAndLogError(Error):
    def __init__(self, error):
        self.error = error
        msg = str(error)
        if hasattr(error, 'stdout') and len(error.stdout):
            msg += "\nstdout:\n{}".format(error.stdout)
        if hasattr(error, 'stderr') and len(error.stderr):
            msg += "\nstderr:\n{}".format(error.stderr)
        super(CmdAndLogError, self).__init__(msg=msg)

class DependencyError(Error):
    def __init__(self, msg, dependency):
        self.dependency = dependency
        msg = "{}\n{}".format(msg, dependency)
        super(DependencyError, self).__init__(msg=msg)

#class MetaError(Error):
#    """Special error to wrap errors that might have occurred previously"""
#    def __init__(self, msg, dependency):
#        self.dependency = dependency
#        if depedency.previous_errors:
#        msg = "{}\n{}".format(msg, dependency)
#        super(DependencyError, self).__init__(msg=msg)
