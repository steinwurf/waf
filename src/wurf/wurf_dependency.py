#! /usr/bin/env python
# encoding: utf-8

import hashlib
import json

class WurfDependency(dict):

    def __init__(self, **kwargs):

        assert "sha1" not in kwargs

        s = json.dumps(kwargs, sort_keys=True)
        sha1 = hashlib.sha1(s.encode('utf-8')).hexdigest()

        super(WurfDependency, self).__init__(sha1=sha1, **kwargs)

    def __getattr__(self, name):
        if name in self:
            return self[name]
        else:
            raise AttributeError("No such attribute: " + name)

    def __setattr__(self, name, value):
        raise AttributeError("Read only")
        #self[name] = value

    def __delattr__(self, name):
        raise AttributeError("Read only")
        # if name in self:
        #     del self[name]
        # else:
        #     raise AttributeError("No such attribute: " + name)
