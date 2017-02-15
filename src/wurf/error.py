#! /usr/bin/env python
# encoding: utf-8

class Error(Exception):
    """Basic exception for errors raised by wurf tools"""
    def __init__(self, msg):
        super(Error, self).__init__(msg)

class CmdAndLogError(Error):
    def __init__(self, error, traceback):
        self.error = error
        self.traceback = traceback
        msg = "Error: {}\nTraceback:{}".format(error, traceback)

        super(CmdAndLogError, self).__init__(msg=msg)

class DependencyError(Error):
    def __init__(self, msg, dependency):
        self.dependency = dependency
        msg = "{}\n{}".format(msg, dependency)
        super(DependencyError, self).__init__(msg=msg)
