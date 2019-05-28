#! /usr/bin/env python
# encoding: utf-8

import contextlib
import re


@contextlib.contextmanager
def rewrite_file(filename):
    class Content:

        def __init__(self):
            self.content = None

        def regex_replace(self, pattern, replacement):
            """ Replace the string matching the pattern in the content with
            the replacement
            """
            updated = re.sub(
                pattern=pattern, repl=replacement, string=self.content)

            if updated == self.content:
                raise RuntimeError("Rewrite failed in {}. Pattern {} not "
                                   "found in file.".format(filename, pattern))

            self.content = updated

    content = Content()

    with open(filename) as f:
        content.content = f.read()

    yield content

    with open(filename, 'w') as f:
        f.write(content.content)
