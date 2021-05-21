#! /usr/bin/env python
# encoding: utf-8


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

        valid_tags = []

        # Get tags with a matching major version
        for tag in tags:
            try:
                t = self.semver.parse(tag)
                if t["major"] != major:
                    continue

                valid_tags.append(tag)
            except ValueError:  # ignore tags we cannot parse
                pass

        if len(valid_tags) == 0:
            return None

        # Now figure out which version is the newest.
        # We only use tags that have the specified major version to ensure
        # compatibility, see rules at semver.org
        best_match = valid_tags[0]

        for t in valid_tags:
            if self.semver.match(best_match, "<" + t):
                best_match = t

        return best_match

    def __repr__(self):
        """
        :return: Representation of this object as a string
        """
        return "%s(%r)" % (self.__class__.__name__, self.__dict__)
