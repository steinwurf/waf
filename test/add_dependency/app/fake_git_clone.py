import os
import shutil

from waflib.extras.wurf.git import Git
from waflib.extras.wurf.error import Error

class CloneError(Error):
    """Basic """
    def __init__(self, repository):
        super(CloneError, self).__init__(
            "No mapping for repository {} found!".format(repository))


class FakeGitClone(Git):

    def __init__(self, git_binary, ctx):
        super(FakeGitClone, self).__init__(git_binary=git_binary, ctx=ctx)

        # This is the directory on the file system which contains the
        # test libraries. We use the url in the clone(...) function
        # to find the library needed

        self.git_dir = ctx.path.parent.find_node('git_dir')

        # This mapping is use when performing a "fake" git clone.
        #
        # In the tests we will make "fake" git repositories available
        # under the 'git_dir' folder using the following mapping.
        # For the a given git URL the value in the dict below gives
        # the directory name in the 'git_dir'.
        self.libraries = {'github.com/acme-corp/foo.git': 'libfoo',
                     'gitlab.com/acme-corp/bar.git': 'libbar',
                     'gitlab.com/acme/baz.git': 'libbaz' }

    def clone(self, repository, directory, cwd):

        dst_directory = os.path.join(cwd, directory)

        for lib_repository, lib_name in self.libraries.items():
            if repository.endswith(lib_repository):

                lib_directory = self.git_dir.find_node(lib_name).abspath()

                shutil.copytree(src=lib_directory, dst=dst_directory,
                    symlinks=True)

                assert os.path.isdir(dst_directory), "We should have a valid path here!"
                return

        else:
            raise CloneError(repository=repository)

    @staticmethod
    def build(registry):
        git_binary = registry.require('git_binary')
        ctx = registry.require('ctx')

        return FakeGitClone(git_binary=git_binary, ctx=ctx)
