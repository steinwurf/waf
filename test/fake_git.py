import os
import shutil
import json
import hashlib
import schema

from waflib.extras.wurf.error import WurfError


def check_git_info(git_info):
    info_schema = schema.Schema(
        {
            "branches": list,
            "tags": list,
            "commits": list,
            "submodules": list,
            "is_detached_head": bool,
            "remote_origin_url": str,
            "checkout": str,
        }
    )

    info_schema.validate(git_info)


def read_git_info(cwd):
    json_path = os.path.join(cwd, "git_info.json")

    with open(json_path) as json_file:
        git_info = json.load(json_file)

    check_git_info(git_info=git_info)

    return git_info


def write_git_info(cwd, git_info):
    check_git_info(git_info=git_info)

    json_path = os.path.join(cwd, "git_info.json")

    with open(json_path, "w") as json_file:
        json.dump(git_info, json_file)


class CloneError(WurfError):
    """Basic"""

    def __init__(self, repository):
        super(CloneError, self).__init__(
            f"No mapping for repository {repository} found!"
        )


class NoClonePathError(WurfError):
    """Basic"""

    def __init__(self, repository):
        super(NoClonePathError, self).__init__(
            f"No clone_path.json available for repository {repository} found!"
        )


class FakeGit:
    def clone(self, repository, directory, cwd):
        if not os.path.isfile("clone_path.json"):
            raise NoClonePathError(repository=repository)

        with open("clone_path.json") as json_file:
            clone_path = json.load(json_file)

        dst_directory = os.path.join(cwd, directory)

        for lib_repository, lib_directory in clone_path.items():
            if repository.endswith(lib_repository):
                shutil.copytree(src=lib_directory, dst=dst_directory, symlinks=True)

                assert os.path.isdir(dst_directory), (
                    "We should have a valid " "path here!"
                )
                return

        else:
            raise CloneError(repository=repository)

    def is_git_repository(self, cwd):
        return os.path.isfile(os.path.join(cwd, "git_info.json"))

    def pull_submodules(self, cwd):
        """Fake a git pull submodule"""

        git_info = read_git_info(cwd=cwd)

        if "submodules" not in git_info:
            return

        for name, path in git_info["submodules"]:
            dst = os.path.join(cwd, name)

            if os.path.isdir(dst):
                # Already exists
                continue

            shutil.copytree(src=path, dst=dst, symlinks=True)

            assert os.path.isdir(dst), "We should have a valid " "path here!"

    def current_commit(self, cwd):
        """Fake the current commit of a repository"""

        git_info = read_git_info(cwd=cwd)

        if git_info["checkout"] in git_info["branches"]:
            return self.checkout_to_commit_id(cwd, git_info["checkout"])

        if git_info["checkout"] in git_info["tags"]:
            return self.checkout_to_commit_id(cwd, git_info["checkout"])

        # The current checkout must already be a commit so we just return
        # it
        return git_info["checkout"]

    def current_tag(self, cwd):
        """Fake the current tag of a repository"""

        git_info = read_git_info(cwd=cwd)

        if git_info["checkout"] in git_info["tags"]:
            return git_info["checkout"]

        return None

    def checkout_to_commit_id(self, cwd, checkout):
        """Fake the commit id from a checkout"""
        git_info = read_git_info(cwd=cwd)
        return self._to_sha1(data=checkout + git_info["remote_origin_url"])

    def tags(self, cwd):
        """Fake what tags are in a repository"""

        git_info = read_git_info(cwd=cwd)
        return git_info["tags"]

    def branches(self, cwd):
        """Fake what branches are in a repository"""

        git_info = read_git_info(cwd=cwd)
        return git_info["branches"]

    def current_branch(self, cwd):
        """ " Fake the current branch of a repository"""

        git_info = read_git_info(cwd=cwd)

        assert (
            git_info["checkout"] in git_info["branches"]
        ), "We are not on a branch it seems"

        return git_info["checkout"]

    def checkout(self, branch, cwd):
        """Fake a git checkout.

        Essentially we can checkout either a branch, tag or commit.

        In FakeGit the commit of a branch or tag will just be the sha1 of the
        branch or tag name.
        """

        git_info = read_git_info(cwd=cwd)

        valid = []
        for tag in git_info["tags"]:
            valid.append(tag)
            valid.append(self._to_sha1(data=tag + git_info["remote_origin_url"]))

        assert branch in valid, f"branch = {branch}, cwd = {cwd}"

        git_info["is_detached_head"] = True
        git_info["checkout"] = branch

        write_git_info(cwd=cwd, git_info=git_info)

    def remote_origin_url(self, cwd):
        """Fake the remote origin url of a repository"""

        git_info = read_git_info(cwd=cwd)
        return git_info["remote_origin_url"]

    def is_detached_head(self, cwd):
        """Fake whether we are in detached_head state

        In git we have a detached state if we checkout something that is not a
        branch. See the checkout(...) function to see how it is updated
        """
        git_info = read_git_info(cwd=cwd)

        return git_info["is_detached_head"]

    def default_branch(self, cwd):
        """Fake the default branch of a repository"""

        git_info = read_git_info(cwd=cwd)
        return git_info.get("default_branch", "master")

    def _to_sha1(self, data):
        """Small private helper to calculate SHA1"""
        return hashlib.sha1(data.encode("utf-8")).hexdigest()

    def is_dirty(self, cwd):
        """Fake whether the repository has uncommitted changes"""
        return False
