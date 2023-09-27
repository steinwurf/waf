from wurf.lock_version_cache import LockVersionCache


def test_calculate_file_hash(testdirectory):
    one = testdirectory.mkdir("one")
    two = testdirectory.mkdir("two")

    def check_hash():
        hash_one = LockVersionCache.calculate_file_hash(one.path())
        hash_two = LockVersionCache.calculate_file_hash(two.path())

        return hash_one == hash_two

    assert check_hash(), "Hash should be the same"

    one.write_text("file1.txt", "hello_world1")
    one.write_text("file2.txt", "hello_world2")
    one.write_text("file3.txt", "hello_world3")

    two.write_text("file1.txt", "hello_world1")
    two.write_text("file2.txt", "hello_world2")
    two.write_text("file3.txt", "hello_world3")

    assert check_hash(), "Hash should be the same"

    one.write_binary("file4.txt", b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09")

    assert not check_hash(), "Hash should be different"

    two.write_binary("file4.txt", b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09")

    assert check_hash(), "Hash should be the same again"

    # check that the filenames are included
    one.write_text("other_name_1.txt", "some text")
    two.write_text("other_name_2.txt", "some text")

    assert not check_hash(), "Hash should be different again"

    two.write_text("other_name_1.txt", "some text")
    one.write_text("other_name_2.txt", "some text")

    assert check_hash(), "Hash should be the same again"

    # Check that nested files are also included
    nested_one = one.mkdir("nested")

    assert not check_hash(), "Hash should be different again"

    nested_two = two.mkdir("nested")

    assert check_hash(), "Hash should be the same again"

    nested_one.write_text("file1.txt", "hello_world1")

    assert not check_hash(), "Hash should be different again"

    nested_two.write_text("file1.txt", "hello_world1")

    assert check_hash(), "Hash should be the same again"


def test_file_hash_persistency(testdirectory):
    testdirectory.write_text("file1.txt", "hello_world1")
    testdirectory.write_text("file2.txt", "hello_world2")
    testdirectory.write_text("file3.txt", "hello_world3")
    testdirectory.write_binary("file4.txt", b"\x05\x06\x07\x08\x09")
    nested = testdirectory.mkdir("nested")
    nested.write_text("file1.txt", "hello_world1337")

    hash = LockVersionCache.calculate_file_hash(testdirectory.path())

    assert hash == "f2a6105558ea3baad7aed7a10fd55cacd7b65e1c", "Hash should match"
