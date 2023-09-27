from wurf.lock_version_cache import LockVersionCache

import hashlib
import os


def test_sha1():
    assert (
        hashlib.sha1(b"hello_world").hexdigest()
        == "e4ecd6fc11898565af24977e992cea0c9c7b7025"
    )

    hash = hashlib.sha1()
    hash.update(b"hello")
    hash.update(b"_")
    hash.update(b"world")

    assert hash.hexdigest() == "e4ecd6fc11898565af24977e992cea0c9c7b7025"


def test_os_walk(testdirectory):
    testdirectory.write_text("a.txt", "a")
    testdirectory.write_text("b.txt", "b")
    testdirectory.write_text("c.txt", "c")
    testdirectory.write_text("d.txt", "d")
    nested = testdirectory.mkdir("nested")
    nested.write_text("e.txt", "e")
    nested.write_text("f.txt", "f")

    items = []
    for _, _, files in os.walk(testdirectory.path()):
        for file in files:
            items.append(file)

    assert len(items) == 6, "Should be 5 files"

    # check the order
    assert items[0].endswith("b.txt")
    assert items[1].endswith("d.txt")
    assert items[2].endswith("a.txt")
    assert items[3].endswith("c.txt")
    assert items[4].endswith("f.txt")
    assert items[5].endswith("e.txt")


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

    assert hash == "15476f1e51243782d38505beacf37e1e5ae1572b", "Hash should match"
