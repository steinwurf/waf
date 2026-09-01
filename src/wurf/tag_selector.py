#! /usr/bin/env python
# encoding: utf-8

import re

# Matches a tag consisting of an optional prefix followed by dot separated
# numbers e.g. "1.2.3", "v1.2.3", "waf-2.0.26" or "1.3.3.7"
TAG_EXPRESSION = re.compile(r"^(?P<prefix>.*?)(?P<version>\d+(\.\d+)*)$")


def split_tag(tag):
    """Split a tag into its prefix and version numbers.

    :param tag: The tag as a string
    :return: A (prefix, version) tuple where version is a tuple of ints, or
        None if the tag does not end in dot separated numbers.
    """
    match = TAG_EXPRESSION.match(tag)

    if not match:
        return None

    version = tuple(int(number) for number in match.group("version").split("."))

    return match.group("prefix"), version


def select_newest_tag(current, tags):
    """Select the newest tag with the same shape as the current tag.

    Only tags using the same prefix and the same numbering style are
    considered, so "2.0.1" will not be selected as an upgrade of "v1.9.0".

    :param current: The tag currently used as a string
    :param tags: The list of available tags
    :return: The newest tag as a string or None if no newer tag was found
    """
    split = split_tag(current)

    if split is None:
        return None

    prefix, newest_version = split
    newest_tag = None

    for tag in tags:
        candidate = split_tag(tag)

        if candidate is None or candidate[0] != prefix:
            continue

        if candidate[1] > newest_version:
            newest_version = candidate[1]
            newest_tag = tag

    return newest_tag
