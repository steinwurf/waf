import json
import os

import mock

from wurf.upgrade import Upgrade


def create_upgrade(names, tags, resolve_json_path):
    git = mock.Mock()
    git.remote_tags.return_value = tags

    git_url_rewriter = mock.Mock()
    git_url_rewriter.rewrite_url = lambda url: url

    return Upgrade(
        ctx=mock.Mock(),
        git=git,
        git_url_rewriter=git_url_rewriter,
        resolve_json_path=resolve_json_path,
        names=names,
    )


def test_upgrade_not_active():
    upgrade = create_upgrade(names=None, tags=[], resolve_json_path="resolve.json")

    assert not upgrade.active()
    assert not upgrade.named("foo")
    assert not upgrade.upgrading("foo")

    with upgrade.recurse(upgrading=False):
        assert not upgrade.upgrading("bar")


def test_upgrade_named():
    upgrade = create_upgrade(names=["foo"], tags=[], resolve_json_path="resolve.json")

    assert upgrade.active()
    assert upgrade.named("foo")
    assert not upgrade.named("bar")

    # The dependencies of an upgraded dependency are upgraded as well
    assert upgrade.upgrading("foo")
    assert not upgrade.upgrading("bar")

    with upgrade.recurse(upgrading=True):
        assert upgrade.upgrading("bar")

    assert not upgrade.upgrading("bar")


def test_upgrade_all():
    upgrade = create_upgrade(names=[], tags=[], resolve_json_path="resolve.json")

    assert upgrade.named("foo")
    assert upgrade.upgrading("bar")
    assert upgrade.unknown() == []


def test_upgrade_unknown():
    upgrade = create_upgrade(names=["foo"], tags=[], resolve_json_path="resolve.json")

    assert upgrade.unknown() == ["foo"]

    dependency = mock.Mock()
    dependency.name = "foo"
    upgrade.add(dependency=dependency, lock_entry=None)

    assert upgrade.unknown() == []


def test_upgrade_checkout(testdirectory):
    dependencies = [
        {
            "name": "foo",
            "resolver": "git",
            "method": "checkout",
            "checkout": "1.0.0",
            "source": "github.com/acme-corp/foo.git",
        },
        {
            "name": "bar",
            "resolver": "git",
            "method": "checkout",
            "checkout": "master",
            "source": "github.com/acme-corp/bar.git",
        },
        {
            "name": "baz",
            "resolver": "git",
            "method": "semver",
            "major": 1,
            "source": "github.com/acme-corp/baz.git",
        },
    ]

    resolve_json_path = os.path.join(testdirectory.path(), "resolve.json")

    with open(resolve_json_path, "w") as resolve_file:
        json.dump(dependencies, resolve_file, indent=4)

    upgrade = create_upgrade(
        names=[],
        tags=["1.0.0", "1.1.0", "master"],
        resolve_json_path=resolve_json_path,
    )

    # The tag is upgraded to the newest tag
    assert upgrade.upgrade_checkout(dependency_args=dependencies[0])["checkout"] == (
        "1.1.0"
    )

    # A branch and a semver dependency are left alone
    assert upgrade.upgrade_checkout(dependency_args=dependencies[1]) == dependencies[1]
    assert upgrade.upgrade_checkout(dependency_args=dependencies[2]) == dependencies[2]

    upgrade.write()

    with open(resolve_json_path, "r") as resolve_file:
        resolve_json = json.load(resolve_file)

    assert resolve_json[0]["checkout"] == "1.1.0"
    assert resolve_json[1]["checkout"] == "master"
