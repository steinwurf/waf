from wurf.git_url_parser import GitUrlParser


def test_git_url_parser_no_protocol():

    parser = GitUrlParser()
    url = parser.parse('github.com/steinwurf/gtest.git')

    assert url.protocol == None
    assert url.host == 'github.com'
    assert url.path == 'steinwurf/gtest'


def test_git_url_parser_https():

    parser = GitUrlParser()
    url = parser.parse('https://github.com/steinwurf/waf.git')

    assert url.protocol == 'https://'
    assert url.host == 'github.com'
    assert url.path == 'steinwurf/waf'


def test_git_url_parser_git_at():

    parser = GitUrlParser()
    url = parser.parse('git@gitlab.com:steinwurf/links.git')

    assert url.protocol == 'git@'
    assert url.host == 'gitlab.com'
    assert url.path == 'steinwurf/links'


def test_git_url_parser_git():

    parser = GitUrlParser()
    url = parser.parse('git://gitlab.com/steinwurf/score.git')

    assert url.protocol == 'git://'
    assert url.host == 'gitlab.com'
    assert url.path == 'steinwurf/score'
