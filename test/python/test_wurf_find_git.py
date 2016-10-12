import pytest
import shutilwhich

def test_wurf_find_git():
    """ This unit test is a bit special in the sense that we are just checking
    to see if we can find the git executable somewhere.

    On all systems we use we should be able to find the git executable.
    Otherwise our waf will not work there.
    """

    path = shutilwhich.which('git')

    assert(path is not None)
