#! /usr/bin/env python
# encoding: utf-8

import hashlib

def wurf_determine_git_directory(name, checkout, source):

        # Use the first 6 characters of the SHA1 hash of the repository url
        # to uniquely identify the repository
        sha1 = hashlib.sha1(source.encode('utf-8')).hexdigest()[:6]

        # The directory for this source
        return name + '-' + checkout + '-' + sha1
