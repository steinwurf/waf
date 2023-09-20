#!/usr/bin/env python
# encoding: utf-8

import os
import json
import pytest
from pytest_testdirectory.runresulterror import RunResultError


""" Integration testing of adding a dependency.

This test is a bit involved so lets try to explain what it does:

We are setting up the following dependency graph:

           +--------------+
           |     app      |----optional----+
           +---+------+---+                |
               |      |               +----+-----+
               |      |               | libextra |
      +--------+      +-------+       +----+-----+
      |                       |
      v                       v
+-----+------+          +-----+-----+   submodule  +--------+
|  libfoo    |          |  libbaz   | +----------> | libqux |
+-----+------+          +-----+-----+              +--------+
      |                       ^
      v                       |
+-----+------+                |
|  libbar    |----------------+
+------------+

The arrows indicate dependencies, so:

- 'app' depends on 'libfoo' and 'libbaz'(internal)
- 'libfoo' depends on 'libbar'
- 'libbar' depends on 'libbaz'

"""


def mkdir_app(directory):
    app_dir = directory.mkdir("app")
    app_dir.copy_file("test/add_dependency/app/main.cpp")
    app_dir.copy_file("test/add_dependency/app/wscript")
    app_dir.copy_file("test/add_dependency/app/resolve.json")

    app_dir.copy_file("test/fake_git.py")

    app_dir.copy_file("build/waf")

    git_info = {
        "checkout": "master",
        "branches": ["master"],
        "commits": [],
        "remote_origin_url": "git@github.com/acme-corp/app.git",
        "is_detached_head": False,
        "submodules": [],
        "tags": [],
    }
    json_path = os.path.join(app_dir.path(), "git_info.json")

    with open(json_path, "w") as json_file:
        json.dump(git_info, json_file)

    return app_dir


def mkdir_libfoo(directory):
    # Add foo dir
    foo_dir = directory.copy_dir(directory="test/add_dependency/libfoo")

    git_info = {
        "checkout": "master",
        "branches": ["master"],
        "commits": [],
        "remote_origin_url": "git@github.com/acme-corp/foo.git",
        "is_detached_head": False,
        "submodules": [],
        "tags": ["v1.2.3", "2.3.3.7", "1.3.3.7"],
    }

    json_path = os.path.join(foo_dir.path(), "git_info.json")

    with open(json_path, "w") as json_file:
        json.dump(git_info, json_file)

    return foo_dir


def mkdir_libextra(directory):
    # Add extra dir
    extra_dir = directory.mkdir("libextra")
    extra_dir.copy_file("test/add_dependency/libextra/wscript")
    extra_dir.copy_dir(directory="test/add_dependency/libextra/src")

    git_info = {
        "checkout": "master",
        "branches": ["master"],
        "commits": [],
        "remote_origin_url": "git@github.com/acme-corp/extra.git",
        "is_detached_head": False,
        "submodules": [],
        "tags": ["2.0.1", "2.0.0"],
    }

    json_path = os.path.join(extra_dir.path(), "git_info.json")

    with open(json_path, "w") as json_file:
        json.dump(git_info, json_file)

    return extra_dir


def mkdir_libbar(directory):
    # Add bar dir
    bar_dir = directory.copy_dir(directory="test/add_dependency/libbar")

    git_info = {
        "checkout": "master",
        "branches": ["master"],
        "commits": [],
        "remote_origin_url": "git@github.com/acme-corp/bar.git",
        "is_detached_head": False,
        "submodules": [],
        "tags": ["someh4sh"],
    }

    json_path = os.path.join(bar_dir.path(), "git_info.json")

    with open(json_path, "w") as json_file:
        json.dump(git_info, json_file)

    return bar_dir


def mkdir_libqux(directory):
    # Add qux dir
    qux_dir = directory.mkdir("libqux")
    qux_dir.write_text(filename="ok.txt", data="hello world", encoding="utf-8")

    git_info = {
        "checkout": "master",
        "branches": ["master"],
        "commits": [],
        "remote_origin_url": "git@github.com/acme/qux.git",
        "is_detached_head": False,
        "submodules": [],
        "tags": [],
    }

    json_path = os.path.join(qux_dir.path(), "git_info.json")

    with open(json_path, "w") as json_file:
        json.dump(git_info, json_file)

    return qux_dir


def mkdir_libbaz(directory, qux_dir):
    # Add baz dir
    baz_dir = directory.copy_dir(directory="test/add_dependency/libbaz")

    git_info = {
        "checkout": "master",
        "branches": ["master"],
        "commits": [],
        "remote_origin_url": "git@github.com/acme/baz.git",
        "is_detached_head": False,
        "submodules": [("libqux", qux_dir.path())],
        "tags": ["3.1.2", "3.2.0", "3.3.0", "3.3.1", "4.0.0"],
    }

    json_path = os.path.join(baz_dir.path(), "git_info.json")

    with open(json_path, "w") as json_file:
        json.dump(git_info, json_file)

    return baz_dir


def run_commands(app_dir, git_dir):
    # Note that waf "climbs" directories to find a lock file in higher
    # directories, and this test is executed within a subfolder of the
    # project's main folder (that already has a lock file). To prevent this
    # behavior, we need to invoke help with the NOCLIMB variable.
    env = dict(os.environ)

    print(f'PATH {env["PATH"]}')

    env["NOCLIMB"] = "1"
    app_dir.run(["python", "waf", "--help"], env=env)

    # We should be able to use --foo_magic_option that is defined in 'foo'
    app_dir.run(
        [
            "python",
            "waf",
            "configure",
            "-v",
            "--foo_magic_option=xyz",
            "--resolve_path",
            "resolved_dependencies",
        ]
    )

    # After configure, the help text should include the description of
    # --foo_magic_option (defined in the 'foo' wscript)
    r = app_dir.run(["python", "waf", "--help"])
    assert r.stdout.match("*Magic option for foo*")

    # The symlink to 'current_build' should be created
    assert os.path.exists(os.path.join(app_dir.path(), "build_current"))

    # The symlinks should be available to all dependencies
    assert os.path.exists(os.path.join(app_dir.path(), "resolve_symlinks", "foo"))
    assert os.path.exists(os.path.join(app_dir.path(), "resolve_symlinks", "baz"))
    assert os.path.exists(os.path.join(app_dir.path(), "resolve_symlinks", "bar"))

    # Also check that libbaz submodule was cloned
    assert os.path.exists(
        os.path.join(app_dir.path(), "resolve_symlinks", "baz", "libqux")
    )

    app_dir.run(["python", "waf", "build", "-v"])

    # Test the zones print
    r = app_dir.run(["python", "waf", "build", "-v", "--zones=resolve"])

    assert r.stdout.match("* resolve recurse foo *")
    assert r.stdout.match("* resolve recurse baz *")
    assert r.stdout.match("* resolve recurse bar *")

    # Try the use checkout
    app_dir.run(
        [
            "python",
            "waf",
            "configure",
            "-v",
            "--baz_checkout=4.0.0",
            "--resolve_path",
            "resolved_dependencies",
        ]
    )
    app_dir.run(["python", "waf", "build", "-v"])

    # Lets remove the resolved dependencies
    resolve_dir = app_dir.join("resolved_dependencies")
    resolve_dir.rmdir()

    # Test the --lock_versions options
    app_dir.run(
        [
            "python",
            "waf",
            "configure",
            "-v",
            "--lock_versions",
            "--resolve_path",
            "resolved_dependencies",
        ]
    )
    assert app_dir.contains_file("lock_version_resolve.json")

    # The symlinks should be available to all dependencies
    assert os.path.exists(os.path.join(app_dir.path(), "resolve_symlinks", "foo"))
    assert os.path.exists(os.path.join(app_dir.path(), "resolve_symlinks", "baz"))
    assert os.path.exists(os.path.join(app_dir.path(), "resolve_symlinks", "bar"))

    app_dir.run(["python", "waf", "build", "-v"])

    resolve_dir = app_dir.join("resolved_dependencies")
    assert resolve_dir.contains_dir("foo-*", "1.3.3.7-*")
    assert resolve_dir.contains_dir("baz-*", "3.3.1-*")
    assert resolve_dir.contains_dir("bar-*", "someh4sh-*")

    resolve_dir.rmdir()

    # This configure should happen from the lock
    app_dir.run(
        ["python", "waf", "configure", "-v", "--resolve_path", "resolved_dependencies"]
    )

    assert app_dir.contains_dir("resolve_symlinks", "foo")
    assert app_dir.contains_dir("resolve_symlinks", "baz")
    assert app_dir.contains_dir("resolve_symlinks", "bar")

    app_dir.run(["python", "waf", "build", "-v"])

    lock_path = os.path.join(app_dir.path(), "lock_version_resolve.json")
    with open(lock_path, "r") as lock_file:
        lock = json.load(lock_file)

    resolve_dir = app_dir.join("resolved_dependencies")

    # The content of resolved dependencies is intersting now :)
    # We've just resolved from the lock resolve file
    # containing the versions needed.

    # foo should use the commit id in the lock file
    assert resolve_dir.contains_dir("foo-*", f'{lock["foo"]["checkout"]}-*')
    # bar is locked to the same commit as the master so it will
    # skip the git checkout and just return the master path
    assert resolve_dir.contains_dir("bar-*", "master-*")
    # baz has its tag in the lock file, so it will be available there
    assert resolve_dir.contains_dir("baz-*", "3.3.1-*")

    app_dir.rmfile("lock_version_resolve.json")
    resolve_dir.rmdir()

    # Test the --lock_paths options
    app_dir.run(
        ["python", "waf", "configure", "-v", "--lock_paths", "--resolve_path", "locked"]
    )

    assert app_dir.contains_dir("resolve_symlinks", "foo")
    assert app_dir.contains_dir("resolve_symlinks", "baz")
    assert app_dir.contains_dir("resolve_symlinks", "bar")

    assert app_dir.contains_file("lock_path_resolve.json")
    app_dir.run(["python", "waf", "build", "-v"])

    # This configure should happen from the lock
    # Now we can delete the git folders - as we should be able to configure
    # from the frozen dependencies
    app_dir.run(
        ["python", "waf", "configure", "-v", "--resolve_path", "resolved_dependencies"]
    )

    assert app_dir.contains_dir("resolve_symlinks", "foo")
    assert app_dir.contains_dir("resolve_symlinks", "baz")
    assert app_dir.contains_dir("resolve_symlinks", "bar")

    # We have the lock file so the resolve_path is not used.
    assert not app_dir.contains_file("resolved_depdendencies")

    lock_path = os.path.join(app_dir.path(), "lock_path_resolve.json")
    with open(lock_path, "r") as lock_file:
        lock = json.load(lock_file)

    assert "locked" in lock["foo"]["path"]
    assert "locked" in lock["bar"]["path"]
    assert "locked" in lock["baz"]["path"]

    app_dir.run(["python", "waf", "build", "-v"])


def test_resolve(testdirectory):
    """Tests that dependencies declared in the wscript works. I.e. where we
    call add_dependency(...) in the resolve function of the wscript.
    """

    app_dir = mkdir_app(directory=testdirectory)

    # Make a directory where we place the libraries that we would have cloned
    # if we had use the full waf resolve functionality.
    #
    # To avoid relying on network connectivity we simply place the
    # libraries there and then fake the git clone step.
    git_dir = testdirectory.mkdir(directory="git_dir")

    qux_dir = mkdir_libqux(directory=git_dir)
    foo_dir = mkdir_libfoo(directory=git_dir)
    bar_dir = mkdir_libbar(directory=git_dir)
    baz_dir = mkdir_libbaz(directory=git_dir, qux_dir=qux_dir)
    extra_dir = mkdir_libextra(directory=git_dir)

    # Instead of doing an actual Git clone - we fake it and use the paths in
    # this mapping
    clone_path = {
        "acme-corp/foo.git": foo_dir.path(),
        "acme-corp/bar.git": bar_dir.path(),
        "acme/baz.git": baz_dir.path(),
        "acme-corp/extra.git": extra_dir.path(),
    }

    json_path = os.path.join(app_dir.path(), "clone_path.json")

    with open(json_path, "w") as json_file:
        json.dump(clone_path, json_file)

    run_commands(app_dir=app_dir, git_dir=git_dir)


def test_add_dependency_path(testdirectory):
    app_dir = mkdir_app(directory=testdirectory)

    git_dir = testdirectory.mkdir(directory="git_dir")

    qux_dir = mkdir_libqux(directory=git_dir)
    foo_dir = mkdir_libfoo(directory=git_dir)
    bar_dir = mkdir_libbar(directory=git_dir)
    extra_dir = mkdir_libextra(directory=git_dir)

    # Instead of doing an actual Git clone - we fake it and use the paths in
    # this mapping
    clone_path = {
        "acme-corp/foo.git": foo_dir.path(),
        "acme-corp/bar.git": bar_dir.path(),
        "acme-corp/extra.git": extra_dir.path(),
    }

    json_path = os.path.join(app_dir.path(), "clone_path.json")

    with open(json_path, "w") as json_file:
        json.dump(clone_path, json_file)

    # Test the --baz-path option: by not putting this dependency in the
    # git_dir, we make sure that our fake git clone step in the wscript
    # cannot find it. Therefore the test will fail if it tries to clone baz.
    path_test = testdirectory.mkdir(directory="path_test")
    baz_dir = mkdir_libbaz(directory=path_test, qux_dir=qux_dir)

    app_dir.run(
        [
            "python",
            "waf",
            "configure",
            "-v",
            f"--baz_path={baz_dir.path()}",
            "--resolve_path",
            "resolved_dependencies",
        ]
    )

    # The symlinks should be available to all dependencies
    assert os.path.exists(os.path.join(app_dir.path(), "resolve_symlinks", "foo"))
    assert os.path.exists(os.path.join(app_dir.path(), "resolve_symlinks", "baz"))
    assert os.path.exists(os.path.join(app_dir.path(), "resolve_symlinks", "bar"))

    app_dir.run(["python", "waf", "build", "-v"])


def test_create_standalone_archive(testdirectory):
    app_dir = mkdir_app(directory=testdirectory)

    git_dir = testdirectory.mkdir(directory="git_dir")

    qux_dir = mkdir_libqux(directory=git_dir)
    foo_dir = mkdir_libfoo(directory=git_dir)
    bar_dir = mkdir_libbar(directory=git_dir)
    baz_dir = mkdir_libbaz(directory=git_dir, qux_dir=qux_dir)
    extra_dir = mkdir_libextra(directory=git_dir)

    # Instead of doing an actual Git clone - we fake it and use the paths in
    # this mapping
    clone_path = {
        "acme-corp/foo.git": foo_dir.path(),
        "acme-corp/bar.git": bar_dir.path(),
        "acme/baz.git": baz_dir.path(),
        "acme-corp/extra.git": extra_dir.path(),
    }

    json_path = os.path.join(app_dir.path(), "clone_path.json")

    with open(json_path, "w") as json_file:
        json.dump(clone_path, json_file)

    app_dir.run(
        [
            "python",
            "waf",
            "configure",
            "-v",
            "--lock_paths",
            "--resolve_path",
            "resolved_dependencies",
        ]
    )
    app_dir.run(["python", "waf", "-v", "standalone"])
    assert app_dir.contains_file("test_add_dependency-1.0.0.zip")


def test_resolve_only(testdirectory):
    app_dir = mkdir_app(directory=testdirectory)

    git_dir = testdirectory.mkdir(directory="git_dir")

    qux_dir = mkdir_libqux(directory=git_dir)
    foo_dir = mkdir_libfoo(directory=git_dir)
    bar_dir = mkdir_libbar(directory=git_dir)
    baz_dir = mkdir_libbaz(directory=git_dir, qux_dir=qux_dir)
    extra_dir = mkdir_libextra(directory=git_dir)

    # Instead of doing an actual Git clone - we fake it and use the paths in
    # this mapping
    clone_path = {
        "acme-corp/foo.git": foo_dir.path(),
        "acme-corp/bar.git": bar_dir.path(),
        "acme/baz.git": baz_dir.path(),
        "acme-corp/extra.git": extra_dir.path(),
    }

    json_path = os.path.join(app_dir.path(), "clone_path.json")

    with open(json_path, "w") as json_file:
        json.dump(clone_path, json_file)

    env = dict(os.environ)
    env["NOCLIMB"] = "1"

    app_dir.run(
        ["python", "waf", "resolve", "--resolve_path", "resolved_dependencies"], env=env
    )

    # The symlinks should be available to all dependencies
    assert os.path.exists(os.path.join(app_dir.path(), "resolve_symlinks", "foo"))
    assert os.path.exists(os.path.join(app_dir.path(), "resolve_symlinks", "baz"))
    assert os.path.exists(os.path.join(app_dir.path(), "resolve_symlinks", "bar"))


def test_lock_versions_and_then_paths(testdirectory):
    app_dir = mkdir_app(directory=testdirectory)

    git_dir = testdirectory.mkdir(directory="git_dir")

    qux_dir = mkdir_libqux(directory=git_dir)
    foo_dir = mkdir_libfoo(directory=git_dir)
    bar_dir = mkdir_libbar(directory=git_dir)
    baz_dir = mkdir_libbaz(directory=git_dir, qux_dir=qux_dir)
    extra_dir = mkdir_libextra(directory=git_dir)

    # Instead of doing an actual Git clone - we fake it and use the paths in
    # this mapping
    clone_path = {
        "acme-corp/foo.git": foo_dir.path(),
        "acme-corp/bar.git": bar_dir.path(),
        "acme/baz.git": baz_dir.path(),
        "acme-corp/extra.git": extra_dir.path(),
    }

    with open(os.path.join(app_dir.path(), "clone_path.json"), "w") as json_file:
        json.dump(clone_path, json_file)

    # Check that we cannot run both lock_versions and lock_paths
    with pytest.raises(RunResultError):
        r = app_dir.run(
            [
                "python",
                "waf",
                "configure",
                "-v",
                "--lock_versions",
                "--lock_paths",
                "--resolve_path",
                "resolved_dependencies",
            ],
        )
        r.stderr.match("*Incompatible options*")

    # Check that we cannot lock versions or paths while using --skip_internal
    with pytest.raises(RunResultError):
        r = app_dir.run(
            [
                "python",
                "waf",
                "configure",
                "-v",
                "--skip_internal",
                "--lock_versions",
                "--resolve_path",
                "resolved_dependencies",
            ],
        )
        r.stderr.match("*Incompatible options*")
    with pytest.raises(RunResultError):
        r = app_dir.run(
            [
                "python",
                "waf",
                "configure",
                "-v",
                "--skip_internal",
                "--lock_path",
                "--resolve_path",
                "resolved_dependencies",
            ],
        )
        r.stderr.match("*Incompatible options*")

    app_dir.run(
        [
            "python",
            "waf",
            "configure",
            "-v",
            "--lock_versions",
            "--resolve_path",
            "resolved_dependencies",
        ]
    )

    assert app_dir.contains_file("lock_version_resolve.json")

    with open(
        os.path.join(app_dir.path(), "lock_version_resolve.json"), "r"
    ) as json_file:
        lock = json.load(json_file)
        assert lock["foo"]["checkout"] == "1.3.3.7"
        assert lock["bar"]["checkout"] == "someh4sh"
        assert lock["baz"]["checkout"] == "3.3.1"

    r = app_dir.run(
        [
            "python",
            "waf",
            "configure",
            "--resolve_path",
            "resolved_dependencies",
        ]
    )

    assert r.stdout.match('*Resolve "baz" (lock/git checkout)*')
    assert r.stdout.match("*resolved_dependencies/baz-*/054dae9d64*")

    # Create a new minor "release" of baz and check that we keep the old
    # version

    json_path = os.path.join(baz_dir.path(), "git_info.json")

    with open(json_path, "r") as json_file:
        git_info = json.load(json_file)
        git_info["tags"].insert(git_info["tags"].index("3.3.1") + 1, "3.3.2")
    with open(json_path, "w") as json_file:
        json.dump(git_info, json_file)

    # Because of the way the fake git works we need to remove the resolved_dependencies
    # folder to make sure that we actually resolve the dependencies again
    app_dir.join("resolved_dependencies").rmdir()

    r = app_dir.run(
        [
            "python",
            "waf",
            "configure",
            "--resolve_path",
            "resolved_dependencies",
        ]
    )

    assert r.stdout.match('*Resolve "baz" (lock/git checkout)*')
    assert r.stdout.match("*resolved_dependencies/baz-*/3.3.1-*")

    # Check that if we remove the lock file, we get the new version
    app_dir.rmfile("lock_version_resolve.json")

    # Because of the way the fake git works we need to remove the resolved_dependencies
    # folder to make sure that we actually resolve the dependencies again
    app_dir.join("resolved_dependencies").rmdir()

    r = app_dir.run(
        [
            "python",
            "waf",
            "-v",
            "configure",
            "--resolve_path",
            "resolved_dependencies",
        ]
    )

    assert r.stdout.match('*Resolve "baz" (git semver)*')
    assert r.stdout.match("*resolved_dependencies/baz-*/3.3.2-*")

    app_dir.run(
        [
            "python",
            "waf",
            "configure",
            "-v",
            "--lock_versions",
            "--resolve_path",
            "resolved_dependencies",
        ]
    )

    app_dir.run(
        [
            "python",
            "waf",
            "configure",
            "-v",
            "--lock_path",
            "--resolve_path",
            "resolved_dependencies",
        ]
    )

    assert app_dir.contains_file("lock_version_resolve.json")
    assert app_dir.contains_file("lock_path_resolve.json")


def test_optional(testdirectory):
    app_dir = mkdir_app(directory=testdirectory)

    git_dir = testdirectory.mkdir(directory="git_dir")

    qux_dir = mkdir_libqux(directory=git_dir)
    foo_dir = mkdir_libfoo(directory=git_dir)
    bar_dir = mkdir_libbar(directory=git_dir)
    baz_dir = mkdir_libbaz(directory=git_dir, qux_dir=qux_dir)
    extra_dir = mkdir_libextra(directory=git_dir)

    # Instead of doing an actual Git clone - we fake it and use the paths in
    # this mapping
    clone_path = {
        "acme-corp/foo.git": foo_dir.path(),
        "acme-corp/bar.git": bar_dir.path(),
        "acme/baz.git": baz_dir.path(),
        "acme-corp/extra.git": extra_dir.path(),
    }

    with open(os.path.join(app_dir.path(), "clone_path.json"), "w") as json_file:
        json.dump(clone_path, json_file)

    r = app_dir.run(
        [
            "python",
            "waf",
            "configure",
            "-v",
            "--resolve_path",
            "resolved_dependencies",
        ],
    )

    assert not r.stdout.match('*Resolve "extra" (git semver)*')

    r = app_dir.run(
        [
            "python",
            "waf",
            "configure",
            "-v",
            "--some_option",
            "--resolve_path",
            "resolved_dependencies",
        ],
    )

    assert r.stdout.match('*Resolve "extra" (git semver)*')
