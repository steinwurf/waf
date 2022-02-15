import os
import shutil
import json

from waflib.extras.wurf.git import Git
from waflib.extras.wurf.error import WurfError


class CloneError(WurfError):
    """Basic"""

    def __init__(self, repository):
        super(CloneError, self).__init__(
            "No mapping for repository {} found!".format(repository)
        )


class FakeGit:

    # def __init__(self):

    #     pass


    def clone(self, repository, directory, cwd):

        print(f"{repository =}")
        print(f"{directory =}")
        print(f"{cwd =}")
        print(f"{os.getcwd() = }")

        with open('clone_path.json') as json_file:
            clone_path = json.load(json_file)

            print(f"{clone_path = }")


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

        print(f"pull_submodules {cwd =}")

    def current_commit(self, cwd):

        print(f"current_commit {cwd =}")

        return "sdfdsfs"

        #print(f"{repository =}")


    def tags(self, cwd):

        print(f"tags {cwd =}")


        return ["sdfds", "aaa"]