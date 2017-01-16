#! /usr/bin/env python
# encoding: utf-8

try:
    # python 2
    from urlparse import urlsplit
except:
    # Python 3 (urlsplit was move in Python 3)
    from urllib.parse import urlsplit

# Nice regex http://stackoverflow.com/a/22312124/1717320

git_schemes = ['https://', 'git@', 'git://']

#def wurf_determine_git_url(url, preferred_scheme):
#    """ Makes sure the Git URL is complete"""
#
#    if not preferred_scheme:
#        preferred_scheme = 'https'
#
#    url = urlsplit(url, scheme=preferred_scheme)
#    return url.geturl()

class GitUrl(object):

    def __init__(self, preferred_scheme = 'https://'):
        self.preferred_scheme = preferred_scheme

    def determine_url(self, url):

        # The repo url cannot contain a protocol handler,
        # because that is added automatically to match the protocol
        # that was used for checking out the parent project
        if url.count('://') > 0 or url.count('@') > 0:
            raise RuntimeError('Repository URL contains the following '
                               'git protocol handler: {}'.format(url))

        if self.preferred_scheme not in git_schemes:
            raise RuntimeError('Unknown git protocol specified: "{}", supported '
                               'protocols are {}'.format(self.preferred_scheme,
                                                         git_schemes))

        if self.preferred_scheme == 'git@':
            # Replace the first / with : in the url to support git over SSH
            # For example, 'github.com/steinwurf/boost.git' becomes
            # 'github.com:steinwurf/boost.git'
            url = url.replace('/', ':', 1)

        return self.preferred_scheme + url
