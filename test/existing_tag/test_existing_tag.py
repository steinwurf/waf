#!/usr/bin/env python
# encoding: utf-8

import os
import json


def mkdir_app(directory):
    app_dir = directory.mkdir("app")
    app_dir.copy_file("test/existing_tag/app/main.cpp")
    app_dir.copy_file("test/existing_tag/app/wscript")
    app_dir.copy_file("test/existing_tag/app/resolve.json")

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


def mkdir_libbaz(directory):
    # Add baz dir
    baz_dir = directory.copy_dir(directory="test/existing_tag/libbaz")

    git_info = {
        "checkout": "master",
        "branches": ["master"],
        "commits": [],
        "remote_origin_url": "git@gitlab.com/acme/baz.git",
        "is_detached_head": False,
        "submodules": [],
        "tags": ["3.1.2"],
    }

    json_path = os.path.join(baz_dir.path(), "git_info.json")

    with open(json_path, "w") as json_file:
        json.dump(git_info, json_file)

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
    clone_path = {"acme/baz.git": baz_dir.path()}

    json_path = os.path.join(app_dir.path(), "clone_path.json")

    with open(json_path, "w") as json_file:
        json.dump(clone_path, json_file)

    app_dir.run(["python", "waf", "configure"])
    app_dir.run(["python", "waf", "build"])
