import pytest
import mock

from wurf import wurf_dependency

def test_wurf_dependency():

    dep = {"name":"waf",
           "optional": True,
           "recurse": False,
           "resolver": "git",
           "method": "checkout",
           "sources":["gitrepo1.git", "gitrepo2.git"]}

    w = wurf_dependency.WurfDependency(**dep)

    assert w.name == "waf"
    assert w.optional == True
    assert w.recurse == False
    assert w.resolver == "git"
    assert w.method == "checkout"
    assert w.sources == ["gitrepo1.git", "gitrepo2.git"]

    # Check there is a sha1 key
    assert "sha1" in w
    assert len(w.sha1) > 0
