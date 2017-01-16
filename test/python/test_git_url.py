import pytest
import mock

#from wurf_determine_git_url import wurf_determine_git_url

def test_wurf_determine_git_url():

    import re


    pattern = re.compile(
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
          [\w/]+      #   Match all alphanumeric characters, including '/'
      )               # End of group

      (               # Group and match the following
        \.git         #   Match '.git'
      )               # End of group

      (               # Group and match the following
        /             #   Match '/'
      )?              # End of group, which is optional
    """, re.VERBOSE)

    r = pattern.match('github.com/steinwurf/gtest.git')
    #r = pattern.match(r"https://github.com/steinwurf/waf.git")
    #r = pattern.match(r"git@github.com:user/project.git")

    if r:
        print("PATH2 {}".format(r.group("protocol")))
        print("PATH2 {}".format(r.group("host")))
        print("PATH2 {}".format(r.group("path")))


    pass
    #res = wurf_determine_git_url('gitlab.com/steinwurf/links.git', 'git://')
    #assert(res == 'git://gitlab.com/steinwurf/links.git')

    #res = wurf_determine_git_url('gitlab.com/steinwurf/links.git', 'git@')
    #assert(res == 'git@gitlab.com:steinwurf/links.git')

    #res = wurf_determine_git_url('gitlab.com/steinwurf/links.git', 'https://')
    #assert(res == 'https://gitlab.com/steinwurf/links.git')

    #res = wurf_determine_git_url('gitlab.com/steinwurf/links.git', None)
    #assert(res == 'https://gitlab.com/steinwurf/links.git')
