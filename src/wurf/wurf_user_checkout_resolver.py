#! /usr/bin/env python
# encoding: utf-8

import hashlib
import os
import shutil
import sys

class WurfUserCheckoutResolver(object):
    """
    User Commit Resolver functionality. Checks out a specific commit.
    """

    def __init__(self, git_checkout_resolver, opt):
        """ Construct a new WurfGitCheckoutResolver instance.

        Args:
            git_checkout_resolver: A WurfGitCheckoutResolver instance.
            opt: A Waf OptionsContext instance.
        """
        self.git_checkout_resolver = git_checkout_resolver
        self.opt = opt
        self.parsed_options = {}

    def __parse_arguement(self, name):

        option = '--%s-use-checkout' % name

        if option in self.parsed_options:
            return self.parsed_options[option]

        self.opt.add_argument(option, default=None, dest=option)

        known_args, unknown_args = self.opt.parse_known_args()

        # Use vars(...) function to convert argparse.Namespace() to dict
        self.parsed_options = vars(known_args)

        return self.parsed_options[option]

    def resolve(self, name, cwd, source, **kwargs):
        """
        Fetches the dependency if necessary.
        :param ctx: A waf ConfigurationContext
        :param path: The path where the dependency should be located
        :param use_checkout: If not None the given checkout will be used
        """

        use_checkout = self.__parse_arguement(name)

        if not use_checkout:
            return

        return self.git_checkout_resolver.resolve(name=name, cwd=cwd,
            source=source, checkout=use_checkout)

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.__dict__)
