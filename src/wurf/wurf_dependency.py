#! /usr/bin/env python
# encoding: utf-8

import hashlib
import json

class WurfDependency(dict):

    def __init__(self, **kwargs):
        """ Construct an instance.

        Basically an small object to store information about a dependency and
        make it available in an easy way.

        Small example (from a dictionary):

            info = {'name': 'foo',
                    'recurse': True,
                    'optional': False,
                    'resolver': 'git',
                    'method': 'checkout',
                    'checkout': '1.3.3.7',
                    'sources': ['github.com/acme-corp/foo.git']}

            # Expand the dict as keyword arguments
            dependency = Dependency(**info)

            # Now we can access the keys as attributes
            assert dependency.name == 'foo'
            assert dependency.recurse == True

        One additional attribute sha1 attribute is added to the dependency. The
        sha1 attribute is a hash of all the dependency information. This allows
        us to e.g. easily compare whether two dependencies with the same name
        in fact equal or whether one has some differnet options.

        Continuing the example from above this is easily quireid using the sha1
        attribute:

            # Access the sha1 attribute
            print("Dependency hash {}".format(dependency.sha1))

        :param kwargs: Keyword arguments containing options for the dependency.
        """

        assert "sha1" not in kwargs

        s = json.dumps(kwargs, sort_keys=True)
        sha1 = hashlib.sha1(s.encode('utf-8')).hexdigest()

        kwargs['sources'] = frozenset(kwargs['sources'])

        super(WurfDependency, self).__init__(sha1=sha1, **kwargs)

    def __getattr__(self, option):
        """ Return the value corresponding to the option.

        :param option: The name of the option to return as a string.
        :return: The option value.
        """

        if option in self:
            return self[option]
        else:
            raise AttributeError("No such attribute: " + option)

    def __setattr__(self, name, value):
        """ Override the __setattr__ function to make the underlying dict
        read-only. We could change this in the future, but it is more to make
        sure that we don't get wierd errors due to some unfortunate unintentional
        modifications.
        """
        raise AttributeError("Read only")

    def __delattr__(self, name):
        """ See __setattr__ docs."""
        raise AttributeError("Read only")

# class WurfDependency(object):
#
#     def __init__(self, **kwargs):
#         """ Construct an instance.
#
#         Basically an small object to store information about a dependency and
#         make it available in an easy way.
#
#         Small example (from a dictionary):
#
#             info = {'name': 'foo',
#                     'recurse': True,
#                     'optional': False,
#                     'resolver': 'git',
#                     'method': 'checkout',
#                     'checkout': '1.3.3.7',
#                     'sources': ['github.com/acme-corp/foo.git']}
#
#             # Expand the dict as keyword arguments
#             dependency = Dependency(**info)
#
#             # Now we can access the keys as attributes
#             assert dependency.name == 'foo'
#             assert dependency.recurse == True
#
#         One additional attribute sha1 attribute is added to the dependency. The
#         sha1 attribute is a hash of all the dependency information. This allows
#         us to e.g. easily compare whether two dependencies with the same name
#         in fact equal or whether one has some differnet options.
#
#         Continuing the example from above this is easily quireid using the sha1
#         attribute:
#
#             # Access the sha1 attribute
#             print("Dependency hash {}".format(dependency.sha1))
#
#         :param kwargs: Keyword arguments containing options for the dependency.
#         """
#
#         assert "sha1" not in kwargs
#
#         s = json.dumps(kwargs, sort_keys=True)
#         sha1 = hashlib.sha1(s.encode('utf-8')).hexdigest()
#
#         self.info = kwargs
#         self.info['sha1'] = sha1
#
#         super(WurfDependency, self).__init__(sha1=sha1, **kwargs)
#
#     def __getattr__(self, option):
#         """ Return the value corresponding to the option.
#
#         :param option: The name of the option to return as a string.
#         :return: The option value.
#         """
#
#         if option in self:
#             return self[option]
#         else:
#             raise AttributeError("No such attribute: " + option)
#
#     def __setattr__(self, name, value):
#         """ Override the __setattr__ function to make the underlying dict
#         read-only. We could change this in the future, but it is more to make
#         sure that we don't get wierd errors due to some unfortunate unintentional
#         modifications.
#         """
#         raise AttributeError("Read only")
#
#     def __delattr__(self, name):
#         """ See __setattr__ docs."""
#         raise AttributeError("Read only")
