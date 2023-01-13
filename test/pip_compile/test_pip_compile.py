def test_pip_compile(testdirectory):

    assert testdirectory.contains_file("requirements.txt") is False

    testdirectory.copy_file("test/pip_compile/wscript")
    testdirectory.copy_file("test/pip_compile/requirements.in")

    testdirectory.copy_file("build/waf")

    testdirectory.run("python waf configure")
    testdirectory.run("python waf build")

    assert testdirectory.contains_file("requirements.txt") is True


def test_pip_compile_rewrite(testdirectory):

    # The requirements.txt file should be rewritten since it contains
    # a wrong hash / signature

    testdirectory.copy_file("test/pip_compile/wscript")
    testdirectory.copy_file("test/pip_compile/requirements.in")
    path = testdirectory.copy_file("test/pip_compile/requirements.txt")

    with open(path, "r") as f:
        old = f.read()

    testdirectory.copy_file("build/waf")

    testdirectory.run("python waf configure")
    testdirectory.run("python waf build")

    with open(path, "r") as f:
        new = f.read()

    assert old != new
