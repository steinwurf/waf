#!/usr/bin/env python
# encoding: utf-8

import os
import json


def mkdir_app(directory):
    app_dir = directory.mkdir("app")
    app_dir.copy_file("test/existing_tag/app/main.cpp")
    app_dir.copy_file("test/existing_tag/app/wscript")

    app_dir.copy_file("test/add_dependency/fake_git_clone.py")
    app_dir.copy_file("build/waf")

    app_dir.run(["git", "init"])

    return app_dir


def mkdir_libbaz(directory):
    # Add baz dir
    baz_dir = directory.copy_dir(directory="test/existing_tag/libbaz")
    baz_dir.run(["git", "init"])
    baz_dir.run(["git", "add", "."])
    baz_dir.run(
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
    baz_dir.run(["git", "tag", "3.1.2"])

    return baz_dir


def test_existing_tag(testdirectory):

    app_dir = mkdir_app(directory=testdirectory)

    # Make a directory where we place the libraries that we would have cloned
    # if we had use the full waf resolve functionality.
    #
    # To avoid relying on network connectivity we simply place the
    # libraries there and then fake the git clone step.
    git_dir = testdirectory.mkdir(directory="git_dir")
    baz_dir = mkdir_libbaz(directory=git_dir)

    # Instead of doing an actual Git clone - we fake it and use the paths in
    # this mapping
    clone_path = {"gitlab.com/steinwurf/baz.git": baz_dir.path()}

    json_path = os.path.join(app_dir.path(), "clone_path.json")

    with open(json_path, "w") as json_file:
        json.dump(clone_path, json_file)

    app_dir.run(["python", "waf", "configure"])
    app_dir.run(["python", "waf", "build"])
