#! /usr/bin/env python
# encoding: utf-8

class MandatoryOptions(object):
    def __init__(self, options):
        self.options = options

    def __getattr__(self, name):

        call = getattr(self.options, name)

        def require(*args, **kwargs):
            value = call(*args, **kwargs)

            if not value:
                raise RuntimeError("WTF Dude")
            return value

        return require
