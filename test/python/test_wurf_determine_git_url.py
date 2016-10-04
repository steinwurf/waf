import pytest
import mock

from wurf_determine_git_url import wurf_determine_git_url

def test_wurf_determine_git_url():

    res = wurf_determine_git_url('gitlab.com/steinwurf/links.git', 'git://')
    assert(res == 'git://gitlab.com/steinwurf/links.git')

    res = wurf_determine_git_url('gitlab.com/steinwurf/links.git', 'git@')
    assert(res == 'git@gitlab.com:steinwurf/links.git')

    res = wurf_determine_git_url('gitlab.com/steinwurf/links.git', 'https://')
    assert(res == 'https://gitlab.com/steinwurf/links.git')

    res = wurf_determine_git_url('gitlab.com/steinwurf/links.git', None)
    assert(res == 'https://gitlab.com/steinwurf/links.git')
