#! /usr/bin/env python
# encoding: utf-8

import re


BASEVERSION = re.compile(
    r"""[vV]?
        (?P<major>0|[1-9]\d*)
        (\.
        (?P<minor>0|[1-9]\d*)
        (\.
            (?P<patch>0|[1-9]\d*)
        )?
        )?
    """,
    re.VERBOSE,
)


class SemverSelector(object):
    """
    Selects the most recent tag for a semver major version.

    Read more about Semantic Versioning here: semver.org
    """

    def __init__(self, semver):
        """Construct an instance.

        :param semver: The semver module
        """
        self.semver = semver

    def select_tag(self, major, tags):
        """
        Enumerate the available tags and return the newest tag for the
        specified major version.

        :param major: The major version number to use as an int.
        :param tags: list of available tags
        :return: the tag to use or None if no tag is compatible
        """
        assert isinstance(major, int), "Major version is not an int"

        valid_tags_ver = dict()

        # Get tags with a matching major version
        for tag_str in tags:
            try:
                tag_ver = self.semver.VersionInfo.parse(tag_str)
            except ValueError:
                # Version might be prefixed with `v` or otherwise not be semver
                # compatible. Try to find a simpler `major.minor.patch` match
                # somewhere in the tag as a last resort.
                tag_ver = self._semver_coerce(tag_str)
            if tag_ver and tag_ver.major == major:
                valid_tags_ver[tag_ver] = tag_str

        if not valid_tags_ver:
            return None

        # Now figure out which version is the newest.
        # We only use tags that have the specified major version to ensure
        # compatibility, see rules at semver.org
        best_match_ver = max(valid_tags_ver.keys())

        # Return original string representation of version tag.
        return valid_tags_ver[best_match_ver]

    def _semver_coerce(self, version):
        """Convert an incomplete version string into a semver-compatible Version
        object

        * Tries to detect a "basic" version string (``major.minor.patch``).
        * If not enough components can be found, missing components are
            set to zero to obtain a valid semver version.

        Copyright (c) 2013, Konstantine Rybnikov
        https://github.com/python-semver/python-semver/

        :param str version: the version string to convert
        :return: a :class:`Version` instance (or ``None`` if it's not a version)
        :rtype: :class:`Version` | None
        """
        # Changed: using `match` instead of `search` to avoid situation where
        # a tag simply containing a number inside it is parsed as a major
        # version.
        match = BASEVERSION.match(version)
        if not match:
            return None

        ver = {
            key: 0 if value is None else int(value)
            for key, value in match.groupdict().items()
        }
        return self.semver.VersionInfo(**ver)

    def __repr__(self):
        """
        :return: Representation of this object as a string
        """
        return "%s(%r)" % (self.__class__.__name__, self.__dict__)
