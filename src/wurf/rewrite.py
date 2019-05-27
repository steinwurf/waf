#! /usr/bin/env python
# encoding: utf-8

import contextlib
import re


@contextlib.contextmanager
def rewrite(filename):
    class Content:

        def __init__(self):
            self.content = None

        def regex_replace(self, pattern, replacement):
            self.content = re.sub(
                pattern=pattern, repl=replacement, string=self.content)

    content = Content()

    with open(filename) as f:
        content.content = f.read()

    yield content

    with open(filename, 'w') as f:
        f.write(content.content)
