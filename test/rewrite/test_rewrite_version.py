def test_rewrite_version(testdirectory):

    in_version = testdirectory.copy_file("test/rewrite/in_version.hpp")
    out_version = testdirectory.copy_file("test/rewrite/out_version.hpp")
    testdirectory.copy_file("test/rewrite/wscript")
    testdirectory.copy_file("build/waf")

    testdirectory.run("python waf configure")
    testdirectory.run("python waf build")

    with open(in_version) as f:
        old = f.read()

    with open(out_version) as f:
        new = f.read()

    assert old == new
