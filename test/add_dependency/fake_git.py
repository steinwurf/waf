import os
import shutil
import json
import hashlib

from waflib.extras.wurf.git import Git
from waflib.extras.wurf.error import WurfError


class CloneError(WurfError):
    """Basic"""

    def __init__(self, repository):
        super(CloneError, self).__init__(
            "No mapping for repository {} found!".format(repository)
        )


class FakeGit:



    def clone(self, repository, directory, cwd):

        print(f"clone {repository =}")
        print(f"clone {directory =}")
        print(f"clone {cwd =}")
        print(f"clone {os.getcwd() = }")

        with open('clone_path.json') as json_file:
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

    def pull_submodules(self, cwd):

        print(f"pull_submodule")

        json_path = os.path.join(cwd, "git_info.json")

        with open(json_path) as json_file:
            git_info = json.load(json_file)

        if "submodules" not in git_info:
            return

        for name, path in git_info["submodules"]:

            dst = os.path.join(cwd, name)

            if os.path.isdir(dst):
                # Already exists
                continue

            shutil.copytree(src=path, dst=dst, symlinks=True)

            assert os.path.isdir(dst), (
                    "We should have a valid " "path here!"
                )


    def current_commit(self, cwd):

        json_path = os.path.join(cwd, "git_info.json")

        with open(json_path) as json_file:
            git_info = json.load(json_file)

        commit = hashlib.sha1(git_info['current_branch'].encode("utf-8")).hexdigest()

        print(f"current_commit => {commit}")

        return commit

    def tags(self, cwd):

        json_path = os.path.join(cwd, "git_info.json")

        with open(json_path) as json_file:
            git_info = json.load(json_file)

        print(f"tags => {git_info['tags']}")

        return git_info['tags']


    def current_branch(self, cwd):

        json_path = os.path.join(cwd, "git_info.json")

        with open(json_path) as json_file:
            git_info = json.load(json_file)

        print(f"current_branch => {git_info['current_branch']}")

        return git_info['current_branch']


    def checkout(self, branch, cwd):

        print(f"checkout => {branch}")


        json_path = os.path.join(cwd, "git_info.json")

        with open(json_path) as json_file:
            git_info = json.load(json_file)

        assert branch in git_info["tags"], f"{branch = }, {cwd =}"

        git_info["is_detached_head"] = True,
        git_info["current_branch"] = branch

        with open(json_path, "w") as json_file:
            json.dump(git_info, json_file)


    def remote_origin_url(self, cwd):

        print(f"remote_origin_url")


        json_path = os.path.join(cwd, "git_info.json")

        with open(json_path) as json_file:
            git_info = json.load(json_file)

        return git_info['remote_origin_url']

    def is_detached_head(self, cwd):

        print(f"is_detached_head")

        json_path = os.path.join(cwd, "git_info.json")

        with open(json_path) as json_file:
            git_info = json.load(json_file)

        return git_info['is_detached_head']

