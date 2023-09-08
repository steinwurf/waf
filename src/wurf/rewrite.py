#! /usr/bin/env python
# encoding: utf-8

import contextlib
import re
import sys


def open_for_writing(filename):
    """
    Helper function to preserve Unix-style line endings (\n) on all platforms
    when writing files. A slightly different solution is required to achieve
    this in Python 2 and 3.

    :param filename: The name of the file to write
    """
    if sys.version_info.major >= 3:
        # Python 3 code in this block
        # The "newline" parameter enforces the given line ending on all
        # platforms. This is not available in Python 2.
        return open(filename, "w", newline="\n")
    else:
        # Python 2 code in this block
        # The only way to force Python 2 to *not* translate line endings to
        # OS-specific separators is using the binary mode. The newlines
        # should be internally represented as \n. If you read lines from an
        # existing file, open the file with "rU" to translate all line
        # endings to \n.
        return open(filename, "wb")


@contextlib.contextmanager
def rewrite_file(filename):
    class Content:
        def __init__(self):
            self.content = None

        def regex_replace(self, pattern, replacement):
            """Replace the string matching the pattern in the content with
            the replacement
            """
            updated, count = re.subn(
                pattern=pattern, repl=replacement, string=self.content
            )

            if count == 0:
                raise RuntimeError(
                    f"Rewrite failed in {filename}. Pattern {pattern} not "
                    f"found in file.\nContent:\n{self.content}"
                )

            self.content = updated

    content = Content()

    # All line endings should be translated to \n when reading the file
    # This is the default behavior in Python 3, but not in Python 2
    flag = "rU" if sys.version_info.major < 3 else "r"
    with open(filename, flag) as f:
        content.content = f.read()

    yield content

    with open_for_writing(filename) as f:
        f.write(content.content)
