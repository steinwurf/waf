#! /usr/bin/env python
# encoding: utf-8

import os
import hashlib


def compile(ctx, requirements_in, requirements_txt):
    """Simple helper function for compiling requirements.txt files from a
    requirements.in file using pip-tools.

    We add a signature to the requirements.txt file to check if the
    requirements.txt file is up to date.

    :param ctx: A Waf Context instance.
    :param requirements_in: Path to the requirements.in file.
    :param requirements_txt: Path to the requirements.txt file.
    """

    # We must have a requirements.in file
    if not os.path.isfile(requirements_in):
        ctx.fatal(
            f"Checking if {requirements_txt} is up to date. However,"
            f" {requirements_in} does not exist"
        )

    # Hash the requirements.in
    sha1 = hashlib.sha1(
        (open(requirements_in, "r").read()).encode("utf-8")
    ).hexdigest()[:6]

    # The signature is used to check if the requirements.txt is up to date
    signature_in = f"# Added by: github.com/steinwurf/waf pip-compile {sha1}\n"

    if os.path.isfile(requirements_txt):

        # Check if the requirements.txt is up to date
        with open(requirements_txt, "r") as f:

            signature_txt = f.readline()

            if signature_in == signature_txt:
                return

        # Remove the old requirements.txt
        os.remove(requirements_txt)

    # Compile the requirements.txt
    with ctx.create_virtualenv() as venv:
        venv.run("python -m pip install pip-tools")
        venv.run(
            "pip-compile {} --output-file {}".format(requirements_in, requirements_txt)
        )

    # Add the signature to the requirements.txt
    with open(requirements_txt, "r+") as f:
        lines = f.readlines()
        lines.insert(0, signature_in)
        f.seek(0)
        f.writelines(lines)
