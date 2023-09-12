import pytest

from wurf.dependency import Dependency


def test_dependency():
    dep = {
        "name": "waf",
        "optional": True,
        "recurse": False,
        "resolver": "git",
        "method": "checkout",
        "checkout": "somebranch",
        "source": "gitrepo.git",
    }

    w = Dependency(**dep)

    assert w.name == "waf"
    assert w.optional is True
    assert w.recurse is False
    assert w.resolver == "git"
    assert w.method == "checkout"
    assert w.checkout == "somebranch"
    assert w.source == "gitrepo.git"

    # Check there is a sha1 key
    assert "sha1" in w
    assert len(w.sha1) > 0

    # Check that we cannot change the read-only attributes (the ones passed
    # at construction time)
    with pytest.raises(Exception):
        w.name = "waf2"

    w.name2 = "waf2"
    assert w.name2 == "waf2"

    assert w.path is None
    assert "path" not in w

    w.rewrite(attribute="method", value="semver", reason="testing it")
    w.rewrite(attribute="major", value=3, reason="testing it")
    w.rewrite(attribute="checkout", value=None, reason="testing it")

    assert w.method == "semver"
    assert w.major == 3
    assert "checkout" not in w


def test_dependency_default_values():
    dep = {
        "name": "foo",
        "resolver": "git",
        "method": "checkout",
        "source": "gitrepo.git",
    }

    w = Dependency(**dep)

    # Check the explicitly defined attributes
    assert w.name == "foo"
    assert w.resolver == "git"
    assert w.method == "checkout"
    assert w.source == "gitrepo.git"

    # Check the default values
    assert w.recurse is True
    assert w.optional is False
    assert w.internal is False

    # Check there is a sha1 key
    assert "sha1" in w
    assert len(w.sha1) > 0
