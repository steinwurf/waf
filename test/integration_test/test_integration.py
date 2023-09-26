#!/usr/bin/env python
# encoding: utf-8

import os
import pytest


@pytest.mark.networktest
def test_kodok_standalone(testdirectory):
    root = testdirectory

    try:
        root.run("git clone git@github.com:steinwurf/kodok.git")
    except Exception:
        # If we couldn't clone the repo, we can't run the test
        # this is probably due to not having sufficient permissions
        # on the machine running the test
        # Lets mark the test as skipped
        pytest.skip("Could not clone kodok repo")

    kodok = root.join("kodok")

    # Checkout a specific version of the kodok repo
    kodok.run("git checkout 20.0.1")

    # Copy the built waf to the repo
    kodok.copy_file("build/waf")

    # Configure and lock the dependencies to specific paths
    r = kodok.run(
        "python waf configure --resolve_path ./resolved_dependencies --lock_path"
    )

    assert r.returncode == 0
    assert r.stdout.match("*finished successfully*")

    # Create a standalone archive
    r = kodok.run("python waf standalone")
    assert r.returncode == 0

    # Check that the standalone archive exists
    standalone_path = os.path.join(kodok.path(), "kodok-20.0.1.zip")
    assert os.path.isfile(standalone_path)

    # Check that we can unpack and build the standalone archive
    standalone = root.mkdir("standalone")
    standalone.run(f"unzip {standalone_path}")
    standalone = standalone.join("kodok-20.0.1")

    # Build the standalone archive
    r = standalone.run("python waf resolve")
    assert r.returncode == 0

    # check that all dependencies are resolved from the paths we specified
    # in the configure step
    for line in r.stdout.output:
        if line.startswith("Resolve "):
            assert "(locked path)" in line
