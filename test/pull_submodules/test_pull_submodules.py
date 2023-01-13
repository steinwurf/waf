#!/usr/bin/env python
# encoding: utf-8

import os
import json

""" Integration testing of adding a dependency.

This test is a bit involved so lets try to explain what it does:

We are setting up the following dependency graph:

           +--------------+
           |     app      |
           +---+------+---+
                  |
                  |
                  |
                  v
            +-----+-----+   submodule  +--------+
            |  libbaz   | +----------> | libqux |
            +-----------+              +--------+


The arrows indicate dependencies, so:

- 'app' depends on  'libbaz'

"""


def mkdir_app(directory, resolve_json):
    app_dir = directory.mkdir("app")
    app_dir.copy_file("test/pull_submodules/app/main.cpp")
    app_dir.copy_file("test/pull_submodules/app/wscript")
    app_dir.copy_file(
        os.path.join("test/pull_submodules/app/", resolve_json),
        rename_as="resolve.json",
    )

    app_dir.copy_file("test/fake_git.py")
    app_dir.copy_file("build/waf")

    # Note: waf will call "git config --get remote.origin.url" in this folder,
    # so "git init" is required to test the default behavior (https resolver)
    # app_dir.run(["git", "init"])
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


def commit_file(directory, filename, content):
    directory.write_text(filename, content, encoding="utf-8")
    directory.run(["git", "add", "."])
    directory.run(
        [
            "git",
            "-c",
            "user.name=John",
            "-c",
            "user.email=doe@email.org",
            "commit",
            "-m",
            "oki",
        ]
    )


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
        "tags": ["3.1.2"],
    }

    json_path = os.path.join(baz_dir.path(), "git_info.json")

    with open(json_path, "w") as json_file:
        json.dump(git_info, json_file)

    return baz_dir


def test_pull_submodule(testdirectory):
    """Tests that submodules are pulled"""

    app_dir = mkdir_app(directory=testdirectory, resolve_json="pull_resolve.json")
    # Make a directory where we place the libraries that we would have cloned
    # if we had use the full waf resolve functionality.
    #
    # To avoid relying on network connectivity we simply place the
    # libraries there and then fake the git clone step.
    git_dir = testdirectory.mkdir(directory="git_dir")

    qux_dir = mkdir_libqux(directory=git_dir)
    baz_dir = mkdir_libbaz(directory=git_dir, qux_dir=qux_dir)

    # Instead of doing an actual Git clone - we fake it and use the paths in
    # this mapping
    clone_path = {"acme/baz.git": baz_dir.path()}

    json_path = os.path.join(app_dir.path(), "clone_path.json")

    with open(json_path, "w") as json_file:
        json.dump(clone_path, json_file)

    # Try the use checkout
    app_dir.run(
        ["python", "waf", "configure", "-v", "--resolve_path", "resolved_dependencies"]
    )
    app_dir.run(["python", "waf", "build", "-v"])

    assert os.path.exists(os.path.join(app_dir.path(), "resolve_symlinks", "baz"))

    assert os.path.exists(
        os.path.join(app_dir.path(), "resolve_symlinks", "baz", "libqux")
    )


def test_no_pull_submodule(testdirectory):
    """Tests that submodules are pulled"""

    app_dir = mkdir_app(directory=testdirectory, resolve_json="no_pull_resolve.json")
    # Make a directory where we place the libraries that we would have cloned
    # if we had use the full waf resolve functionality.
    #
    # To avoid relying on network connectivity we simply place the
    # libraries there and then fake the git clone step.
    git_dir = testdirectory.mkdir(directory="git_dir")

    qux_dir = mkdir_libqux(directory=git_dir)
    baz_dir = mkdir_libbaz(directory=git_dir, qux_dir=qux_dir)

    # Instead of doing an actual Git clone - we fake it and use the paths in
    # this mapping
    clone_path = {"acme/baz.git": baz_dir.path()}

    json_path = os.path.join(app_dir.path(), "clone_path.json")

    with open(json_path, "w") as json_file:
        json.dump(clone_path, json_file)

    # Try the use checkout
    app_dir.run(
        ["python", "waf", "configure", "-v", "--resolve_path", "resolved_dependencies"]
    )
    app_dir.run(["python", "waf", "build", "-v"])

    assert os.path.exists(os.path.join(app_dir.path(), "resolve_symlinks", "baz"))

    assert not os.path.exists(
        os.path.join(app_dir.path(), "resolve_symlinks", "baz", "libqux")
    )
