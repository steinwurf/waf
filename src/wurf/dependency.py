#! /usr/bin/env python
# encoding: utf-8

import hashlib
import json

class Dependency(object):

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

        self.info = kwargs
        self.info['sha1'] = sha1

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
        self.hash = None
        
    def __getattr__(self, option):
        """ Return the value corresponding to the option.

        :param option: The name of the option to return as a string.
        :return: The option value.
        """

        if option in self.info:
            return self.info[option]
        else:
            raise AttributeError("No such attribute: " + option)

    def __contains__(self, option):
        """ Checks if the option is available.
        
        :return: True if the option is available otherwise False
        """
        return option in self.info

    def __str__(self):
        return str(self.info)

    def __hash__(self):
        """ :return: Integer hash value for the dependency. """
        
        if not self.hash:
            self.hash = hash(self.info['sha1'])
        
        return self.hash
