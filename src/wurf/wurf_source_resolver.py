#! /usr/bin/env python
# encoding: utf-8

import argparse
import sys
import os


#           +--------------------------+
#           |   WurfHashDependency     |
#           |                          |
#           |   - Hash the dependency  |
#           |     using sha1.          |
#           +--------------------------+
#               +                   ^
#               |                   |
#       add_dependency(...)        path
#               |                   |
#               v                   +
#      +-----------------------------------+
#      |   WurfDependencyCache             |
#      |                                   |
#      |   - Cache the path and sha1 for   |
#      |     a resolved dependency.        |
#      |   - Store the path and sha1 in a  |
#      |     persistant cache file.        |
#      |   - Checks that if a dependency   |
#      |     is added twice their sha1     |
#      |     must match.                   |
#      |                                   |
#      +-----------------------------------+
#              +                   ^
#              |                   |
#      add_dependency(...)        path
#              |                   |
#              v                   +
#     +------------------------------------+
#     |  WurfUserResolve                   |
#     |                                    |
#     |  - Check if user specified a path  |
#     |    on the command-line.            |
#     |                                    |
#     +------------------------------------+
#              +                   ^
#              |                   |
#      add_dependency(...)        path
#              |                   |
#              v                   +
#    +----------------------------------------+
#    |  WurfFastResolve                       |
#    |                                        |
#    |  - Active if the --fast-resolve option |
#    |    is specified.                       |
#    |  - If the cache file exists            |
#    |    loads the path from there.          |
#    |                                        |
#    +----------------------------------------+
#               +                   ^
#               |                   |
#       add_dependency(...)        path
#               |                   |
#               v                   +
#       +---------------------------------+
#       |  WurfResolve                    |
#       |                                 |
#       |  - Uses the specified resolver  |
#       |    type to fetch the dependency |
#       +---------------------------------+






from . import wurf_error

class WurfSourceError(wurf_error.WurfError):
    """Generic exception for wurf"""
    def __init__(self, name, cwd, resolver, sources, **kwargs):

        self.name = name
        self.cwd = cwd
        self.resolver = resolver
        self.sources = sources
        self.kwargs = kwargs

        super(WurfSourceError, self).__init__("Error resolving sources for {}".format(name))



class WurfSourceResolver(object):
    """
    """

    def __init__(self, user_resolvers, type_resolvers, ctx):
        """ Construct an instance.

        :param user_resolvers: A list of resolvers allowing the user to provide
            the path to a dependency in various ways.

        :param type_resolvers: A dict object mapping source types to resolvers
            instances, providing the resolve(...) function.

                Example:
                    {'git': git_resolver_instance,
                     'ftp': ftp_resolver_instance}

        :param ctx: A Waf Context instance.
        """
        self.user_resolvers = user_resolvers
        self.type_resolvers = type_resolvers
        self.ctx = ctx

    def resolve(self, name, cwd, resolver, sources, **kwargs):
        """ Resolve the dependency.

        - First see if the user has provided some options
        - Then use the specified git method

        :param name: Name of the dependency as a string
        :param cwd: Current working directory as a string
        :param resolver: The type of resolver to use.
        :param sources: List of URLs which can be used for the dependency.
        :param kwargs: Keyword arguments containing options for the dependency

        :return: Path to resolved dependency as a string
        """

        # Try user method
        for r in self.user_resolvers:
            path = r.resolve(name=name, cwd=cwd, resolver=resolver,
                sources=sources, **kwargs)

            if path:
                return path

        # Use resolver
        for source in sources:
            try:
                path = self.__resolve(name, cwd, resolver, source, **kwargs)
            except Exception as e:

                # Using exc_info will attache the current exception information
                # to the log message (including traceback to where the
                # exception was thrown).
                # Waf is using the standard Python Logger so you can check the
                # docs here (read about the exc_info kwargs):
                # https://docs.python.org/2/library/logging.html
                #
                self.ctx.logger.debug("Source {} resolve failed:".format(
                    source), exc_info=True)
            else:
                return path
        else:

            msg = "Error resolving sources for {}:\n".format(name)
            msg += "\tcwd={}\n".format(cwd)
            msg += "\tresolver={}\n".format(resolver)
            msg += "\tkwargs={}\n".format(kwargs)
            msg += "\tsources: {}\n".format(sources)

            self.ctx.logger.debug(msg)

            raise WurfSourceError(name=name, cwd=cwd, resolver=resolver,
                sources=sources, **kwargs)


    def __resolve(self, name, cwd, resolver, source, **kwargs):

        r = self.type_resolvers[resolver]
        return r.resolve(name=name, cwd=cwd, source=source, **kwargs)

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.__dict__)


class WurfSourceResolver2(object):
    """
    """

    def __init__(self, name, resolvers, ctx):
        """ Construct an instance.

        :param user_resolvers: A list of resolvers allowing the user to provide
            the path to a dependency in various ways.

        :param type_resolvers: A list of type resolvers object for the available
           sources

        :param ctx: A Waf Context instance.
        """
        self.name = name
        self.resolvers = resolvers
        self.ctx = ctx

    def resolve(self):
        """ Resolve the dependency.

        :return: Path to resolved dependency as a string
        """

        for resolver in self.resolvers:
            try:
                path = resolver.resolve()
            except Exception as e:

                # Using exc_info will attache the current exception information
                # to the log message (including traceback to where the
                # exception was thrown).
                # Waf is using the standard Python Logger so you can check the
                # docs here (read about the exc_info kwargs):
                # https://docs.python.org/2/library/logging.html
                #
                self.ctx.logger.debug("Source {} resolve failed:".format(
                    resolver), exc_info=True)
            else:
                assert os.path.isdir(path)
                return path
        else:

            msg = "FAILED RESOLVE SOURCE {} check log for detailed information".format(self.name)
            self.ctx.logger.debug(msg)

            raise RuntimeError(msg)

    def __repr__(self):
        """
        :return: Representation of this object as a string
        """
        return "%s(%r)" % (self.__class__.__name__, self.__dict__)

class WurfSourceResolver2(object):
    """
    """

    def __init__(self, name, resolvers, ctx):
        """ Construct an instance.

        :param user_resolvers: A list of resolvers allowing the user to provide
            the path to a dependency in various ways.

        :param type_resolvers: A list of type resolvers object for the available
           sources

        :param ctx: A Waf Context instance.
        """
        self.name = name
        self.resolvers = resolvers
        self.ctx = ctx

    def resolve(self):
        """ Resolve the dependency.

        :return: Path to resolved dependency as a string
        """

        for resolver in self.resolvers:
            try:
                path = resolver.resolve()
            except Exception as e:

                # Using exc_info will attache the current exception information
                # to the log message (including traceback to where the
                # exception was thrown).
                # Waf is using the standard Python Logger so you can check the
                # docs here (read about the exc_info kwargs):
                # https://docs.python.org/2/library/logging.html
                #
                self.ctx.logger.debug("Source {} resolve failed:".format(
                    resolver), exc_info=True)
            else:
                assert os.path.isdir(path)
                return path
        else:

            msg = "FAILED RESOLVE SOURCE {} check log for detailed information".format(self.name)
            self.ctx.logger.debug(msg)

            raise RuntimeError(msg)

    def __repr__(self):
        """
        :return: Representation of this object as a string
        """
        return "%s(%r)" % (self.__class__.__name__, self.__dict__)
