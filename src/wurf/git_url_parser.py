#! /usr/bin/env python
# encoding: utf-8

import re

from .git_url import GitUrl

class GitUrlParser(object):

    def __init__(self):

        self.parser = re.compile(
        r"""
          (?P<protocol>   # Group and match the following (group named "protocol")
            (             #   Group and match the following
              git         #     Match 'git'
              |           #     or
              ssh         #     Match 'ssh'
              |           #     or
              http(s)?    #     Match 'http' followed by 0 or 1 's'
            )             #   End of group
            (             #   Group and match the following
              ://         #     Match '://'
            )             #   End group
            |             # Or
            (             #   Group and match the following
              git@        #     Match 'git@'
            )             #   End of group
          )?              # End of group, which is optional

          (?P<host>       # Group and match the following (group named "host")
            [\w\.]+       #   Followed by one or more letters including '.'
          )               # End of group

          (               # Group and match the following
            :             #   Match ':'
          )?              # End of group, which is optional

          (               # Group and match the initial slash of the path.
            /             #   Match '/'
          )?              # End of group, which is optional

          (?P<path>       # Group and match the following (group named "path")
              [\w\./-]+   #   Match all alphanumeric characters, including '/'
                          #   and '-'and '.'
          )               # End of group

          (               # Group and match the following
            \.git         #   Match '.git'
          )?              # End of group, which is optional

          (               # Group and match the following
            /             #   Match '/'
          )?              # End of group, which is optional
        """, re.VERBOSE)


    def parse(self, url):
        """ Parses the url and returns a GitUrl"""

        result = self.parser.match(url)

        return GitUrl(protocol=result.group('protocol'),
            host=result.group('host'), path=result.group('path'))
