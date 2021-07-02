import os


class FakeUrlDownload(object):
    def __init__(self):
        pass

    def download(self, cwd, source, filename):

        assert not filename
        filename = "lib.cpp"

        file_path = os.path.join(cwd, filename)

        with open(file_path, "w") as the_file:
            the_file.write("Hello\n")

        return file_path

    @staticmethod
    def build(registry):
        return FakeUrlDownload()
