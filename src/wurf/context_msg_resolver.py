#! /usr/bin/env python
# encoding: utf-8


class ContextMsgResolver(object):

    def __init__(self, resolver, ctx, dependency):
        """ Construct an instance.

        :param resolver: The resolver used to fecth the dependency
        :param ctx: A Waf Context instance.
        :param dependency: A Dependency instance.
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
        

        self.ctx.start_msg('{} {}'.format(
            self.dependency.resolver_method, self.dependency.name))

        path = self.resolver.resolve()

        if not path:
            # An optional dependency might be unavailable if the user
            # does not have a license to access the repository, so we just
            # print the status message and continue
            self.ctx.end_msg('Unavailable', color='RED')
        else:
            
            if self.dependency.is_symlink:
                real_path = self.dependency.real_path
                self.ctx.end_msg("{} => {}".format(path, real_path))
            else:
                self.ctx.end_msg(path)

        return path
