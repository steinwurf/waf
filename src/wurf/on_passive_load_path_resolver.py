#! /usr/bin/env python
# encoding: utf-8

import os
import json

class OnPassiveLoadPathResolver(object):

    def __init__(self, ctx, name, sha1, bundle_config_path):
        """ Construct an instance.

        :param ctx: A Waf Context instance.
        :param name: Name of the dependency as a string
        :param sha1: Hash of the depenency information as a string
        :param bundle_config_path: A string containing the path to where the
            dependencies config json files should be / is stored.
        """
        self.ctx = ctx
        self.name = name
        self.sha1 = sha1
        self.bundle_config_path = bundle_config_path

    def resolve(self):
        """ Resolve a path to a dependency.

        If we are doing an "passive" resolver, meaning that waf was not invoked
        with configure. Then we load the resolved path to the file-system.
        Otherwise we raise an exception.

        :return: The path as a string.
        """

        config = self.__read_config()

        if self.sha1 != config['sha1']:
            self.ctx.fatal('Failed sha1 check')

        path = str(config['path'])

        if not os.path.isdir(path):
            self.ctx.fatal('Not valid path {}'.format(path))

        return path

    def __read_config(self):
        """ Read the dependency config from file
        """

        config_path = os.path.join(
            self.bundle_config_path, self.name + '.resolve.json')

        if not os.path.isfile(config_path):
            self.ctx.fatal('No config for {} - re-run configure'.format(
                self.name))

        with open(config_path, 'r') as config_file:
            return json.load(config_file)
            
            
# @todo move to own file
class ContextMsgResolver(object):

    def __init__(self, resolver, ctx, dependency):
        """ Construct an instance.

        :param resolver: The resolver used to fecth the dependency
        :param ctx: A Waf Context instance.
        :param dependency: The Dependency object.
        """
        self.resolver = resolver
        self.ctx = ctx
        self.dependency = dependency
    
    def resolve(self):
        """ Resolve a path to a dependency.

        If we are doing an "passive" resolver, meaning that waf was not invoked
        with configure. Then we load the resolved path to the file-system.
        Otherwise we raise an exception.

        :return: The path as a string.
        """
        
        self.ctx.start_msg('Resolve dependency {}'.format(dependency.name))
        
        path = self.resolver.resolve()
        
        if not path:
            # An optional dependency might be unavailable if the user
            # does not have a license to access the repository, so we just
            # print the status message and continue
            self.ctx.end_msg('Unavailable', color='RED')
        else:
            
            self.ctx.end_msg(path)
            
        return path
        
class OptionalResolver(object):

    def __init__(self, resolver, dependency):
        """ Construct an instance.

        :param resolver: The resolver used to fecth the dependency
        :param dependency: The Dependency object.
        """
        self.resolver = resolver
        self.dependency = dependency
    
    def resolve(self):
        """ Resolve a path to a dependency.

        If we are doing an "passive" resolver, meaning that waf was not invoked
        with configure. Then we load the resolved path to the file-system.
        Otherwise we raise an exception.

        :return: The path as a string.
        """
        
        path = self.resolver.resolve()
        
        if not path and not self.dependency.optional:
            raise RuntimeError("WTF non-optional dependency failed {}".format(
                self.dependency))
            
        return path
            
