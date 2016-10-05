import pytest
import mock

from wurf_determine_git_directory import wurf_determine_git_directory

def test_wurf_determine_git_directory():

    res = wurf_determine_git_directory(
        name='links',
        checkout='mybranch',
        source='https://gitlab.com/steinwurf/links.git')

    assert(res == 'links-mybranch-04aeea')
