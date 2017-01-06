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

    w = wurf_dependency.WurfDependency(dep)

    assert w.name == "waf"
    assert w.optional == True
    assert w.recurse == False
    assert w.resolver == "git"
    assert w.method == "checkout"
    assert w.sources == ["gitrepo1.git", "gitrepo2.git"]

    w["sha1"] = "sd324dsf"

    assert w.sha1 == "sd324dsf"
