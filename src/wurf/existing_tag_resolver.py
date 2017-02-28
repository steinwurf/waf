#! /usr/bin/env python
# encoding: utf-8

import os
import hashlib

class ExistingTagResolver(object):
    """
    Resolves a specific semver version if a compatible tag is already checked
    out, and there is no newer version in the tag database.
    """

    def __init__(self, ctx, dependency, semver_selector, tag_database,
                 bundle_path, sources):
        """ Construct a new ExistingTagResolver instance.

        :param ctx: A Waf Context instance.
        :param dependency: The Dependency object.
        :param semver_selector: A SemverSelector instance.
        :param tag_database: A TagDatabase instance.
        :param bundle_path: Current working directory as a string. This is
            the place where we should create new folders etc.
        :param sources: The URLs of the dependency as a list of strings
        """

        self.ctx = ctx
        self.dependency = dependency
        self.semver_selector = semver_selector
        self.tag_database = tag_database
        self.bundle_path = bundle_path
        self.sources = sources

        assert os.path.isabs(self.bundle_path)

    def resolve(self):
        """
        Resolves the path to an existing checkout folder.

        :return: The path to the existing tag, otherwise None.
        """
        # Query the tags for this dependency from the online database
        project_tags = self.tag_database.project_tags(self.dependency.name)

        if not project_tags:
            return None

        # Select the most recent tag for this major version
        most_recent = self.semver_selector.select_tag(
            self.dependency.major, project_tags)

        for source in self.sources:

            # The tag database only contains information about Steinwurf
            # projects, so skip this if the URL does not contain 'steinwurf'
            if 'steinwurf' not in source:
                continue

            repo_hash = hashlib.sha1(source.encode('utf-8')).hexdigest()[:6]

            # The existing checkouts are stored in this parent folder
            repo_folder = os.path.join(self.bundle_path,
                '{}-{}'.format(self.dependency.name, repo_hash))

            if not os.path.exists(repo_folder):
                continue

            checkouts = [dir for dir in os.listdir(repo_folder)
                         if os.path.isdir(os.path.join(repo_folder, dir))]

            # If the checkout for the most recent tag is available,
            # we return the path to that checkout
            if most_recent in checkouts:
                tag_path = os.path.join(repo_folder, most_recent)

                self.ctx.to_log(
                    'wurf: ExistingTagResolver name {} -> {}'.format(
                        self.dependency.name, tag_path))

                return tag_path

        return None

    def __repr__(self):
        """
        :return: Representation of this object as a string
        """
        return "%s(%r)" % (self.__class__.__name__, self.__dict__)
