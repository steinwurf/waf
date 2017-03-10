#! /usr/bin/env python
# encoding: utf-8

import hashlib
import json
import collections

class Dependency(object):

    def __init__(self, **kwargs):
        """ Construct an instance.

        A small object to store information about a dependency.

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

        The 'sha1' extra attribute is added to the dependency, which is
        a hash value of all the dependency information. This allows
        us to e.g. easily compare whether two dependencies with the same name
        are equal or whether one has some different options.

        Continuing the example from above, this value can be queried using the
        sha1 attribute:

            # Access the sha1 attribute
            print("Dependency hash {}".format(dependency.sha1))

        Additional attributes may be added to the dependency during resolve.
        However, they cannot overwrite the existing attributes created at
        construction time.

        So in the small example from before all the following attributes are
        read-only: name, recurse, optional, resolver, method, checkout,
        sources and sha1.

        Any other attributes can be added and modified as needed. The following
        documents used attributes with reserved meaning:

        - "is_symlink" and "real_path": The "is_symlink" attribute denotes
          whether the path returned by the resolver is a symbolic link. If
          this is the case the "real_path" attribute of the dependency will
          contain the path in the file-system which the symbolic link points
          to.

        - "resolver_chain": This attribute assigns a high-level name to the
          chain of resolvers, such as "Resolve" or "Load". This describes
          the high-level operation of the resolver chain.

        - "resolver_action": This attribute describes the specific action
          taken to resolve the dependency. For example: "git checkout",
          "user path".

        :param kwargs: Keyword arguments containing options for the dependency.
        """
        assert "sha1" not in kwargs

        # Set default values for some common attributes
        if 'recurse' not in kwargs:
            kwargs['recurse'] = True
        if 'optional' not in kwargs:
            kwargs['optional'] = False
        if 'internal' not in kwargs:
            kwargs['internal'] = False

        s = json.dumps(kwargs, sort_keys=True)
        sha1 = hashlib.sha1(s.encode('utf-8')).hexdigest()

        # kwargs is a dict, we add it as an instance attribute.
        object.__setattr__(self, 'read_only', kwargs)
        self.read_only['sha1'] = sha1

        # For some operations like, storing a dependency in a dict as the key
        # it is needed that the dependency is hashable (returned as an integer).
        # This is implemented in the __hash__() member function, which will
        # compute the hash from the sha1 string. We will store this value to
        # avoid computing it over and over.
        #
        # A good question here, is why do we store both the sha1 and another
        # integer hash?
        #
        # The sha1 is stored in config files describing a dependency, so it
        # has to be stable. In the sense that if the config was written using
        # e.g. python2.7 and then read under python3.3 the sha1 must stay the
        # same for a given input.
        #
        # This is guarenteed by the SHA1 algorithm.
        #
        # This guarentee does not seem (we are just not sure) to be implemented
        # for the in-built hash() function. Which could change it's
        # implementation for e.g. hashing strings between interpreter versions.
        #
        # However, we cannot rely only on the SHA1 as it is stored as a string
        # which means it cannot be returned from the __hash__ function (it
        # requires an integer). The simplest solution therefore seemd to be:
        #
        # 1. Use the stable / consistent SHA1 hash for describing a dependency
        #    in external formats such as files
        # 2. Use the Python hash() function to generate a integer hash for
        #    run-time usage (i.e. within the same interpreter session).

        self.read_only['hash'] = None

        # Resolver attributes (modifiable)
        object.__setattr__(self, 'read_write', dict())

    def __getattr__(self, attribute):
        """ Return the value corresponding to the attribute.

        :param attribute: The name of the attribute to return as a string.
        :return: The attribute value, if the attribute does not exist
            return None
        """
        if attribute in self.read_only:
            return self.read_only[attribute]

        elif attribute in self.read_write:
            return self.read_write[attribute]

        else:
            return None

    def __setattr__(self, attribute, value):
        """ Sets a dependency attribute.

        :param attribute: The name of the attribute as a string
        :param value: The value of the attribute
        """
        if attribute in self.read_only:
            raise AttributeError("Attribute {} read-only.".format(attribute))
        else:
            self.read_write[attribute] = value

    def __contains__(self, attribute):
        """ Checks if the attribute is available.

        :return: True if the attribute is available otherwise False
        """
        return (attribute in self.read_only) or (attribute in self.read_write)

    def __str__(self):
        """ :return: String representation of the dependency. """
        return "Dependency\nread only: {}\nread write: {}".format(
            self.read_only, self.read_write)

    def __hash__(self):
        """ :return: Integer hash value for the dependency. """
        if not self.read_only['hash']:
            self.read_only['hash'] = hash(self.read_only['sha1'])

        return self.read_only['hash']
