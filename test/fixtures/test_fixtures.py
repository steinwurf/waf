import os


def test_fixtures(test_directory):
    """ Unit test for the test_directory fixture"""
    assert os.path.exists(test_directory.path())

    sub1 = test_directory.mkdir('sub1')
    assert os.path.exists(sub1.path())

    sub1.write_file('ok.txt', 'hello_world')

    ok_path = os.path.join(sub1.path(), 'ok.txt')

    assert os.path.isfile(ok_path)
    sub1.rmfile('ok.txt')
    assert not os.path.isfile(ok_path)

    sub1.write_file('ok2.txt', 'hello_world2')

    ok_path = os.path.join(sub1.path(), 'ok2.txt')

    assert os.path.isfile(ok_path)

    sub2 = test_directory.mkdir('sub2')
    sub1_copy = sub2.copy_dir(sub1.path())

    assert os.path.exists(os.path.join(sub2.path(), 'sub1'))
    assert os.path.exists(sub1_copy.path())

    # Run a command that should be available on all platforms
    r = sub1.run('python', '--version')

    assert r.returncode == 0
    assert r.stdout.match('Python *') or r.stderr.match('Python *')

    sub3 = test_directory.mkdir('sub3')
    ok3_file = sub3.copy_file(ok_path, rename_as='ok3.txt')

    assert test_directory.contains_dir('sub3')
    assert not test_directory.contains_dir('notheredir')

    assert os.path.isfile(ok3_file)
    assert sub3.contains_file('ok3.txt')
    assert not sub3.contains_file('noherefile.txt')

    sub3.rmdir()
    assert not test_directory.contains_dir('sub3')

    sub4 = test_directory.mkdir('sub4')
    sub4.mkdir('sub5')

    # Will look for 'sub4/sub5'
    assert test_directory.contains_dir('sub4', 'sub5')

    sub5 = sub4.join('sub5')
    sub5.rmdir()

    assert not test_directory.contains_dir('sub4', 'sub5')
