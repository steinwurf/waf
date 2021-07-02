import os
import shutil

from waflib.extras.wurf.git import Git
from waflib.extras.wurf.error import WurfError


class CloneError(WurfError):
    """Basic"""

    def __init__(self, repository):
        super(CloneError, self).__init__(
            "No mapping for repository {} found!".format(repository)
        )


class FakeGitClone(Git):
    def __init__(self, git_binary, ctx, clone_path):
        """Create a new instance.

        :param git_binary: The git executable
        :param ctx: A Waf context instance
        :param clone_path: A dict containg a mapping or git repository URL and
            location on the file system.

            The URL is the key and the file-system path is the value.

            Example:

                clone_path = {'foo.git': '/tmp/libfoo',
                              'bar.git': '/tmp/libbar'}

            Depending on the unit test you can provide more of the URL if e.g.
            certain URLs should fail.

            Example:

                clone_path = {'github.com/acme-corp/foo.git': 'libfoo',
                              'gitlab.com/acme-corp/bar.git': 'libbar'}

            In this case we have no mapping for e.g. bitbucket so all those
            URLs will raise a CloneError (simulating a mirror which is down).

        """
        super(FakeGitClone, self).__init__(git_binary=git_binary, ctx=ctx)

        self.clone_path = clone_path

    def clone(self, repository, directory, cwd):

        dst_directory = os.path.join(cwd, directory)

        for lib_repository, lib_directory in self.clone_path.items():
            if repository.endswith(lib_repository):

                shutil.copytree(src=lib_directory, dst=dst_directory, symlinks=True)

                assert os.path.isdir(dst_directory), (
                    "We should have a valid " "path here!"
                )
                return

        else:
            raise CloneError(repository=repository)

    @staticmethod
    def build(registry):
        git_binary = registry.require("git_binary")
        ctx = registry.require("ctx")
        clone_path = registry.require("clone_path")

        return FakeGitClone(git_binary=git_binary, ctx=ctx, clone_path=clone_path)
