from wurf.git_url_parser import GitUrlParser
from wurf.git_url_rewriter import GitUrlRewriter


def test_git_url_rewriter_https():

    parser = GitUrlParser()
    rewriter = GitUrlRewriter(parser=parser, rewrite_protocol="https://")

    r = rewriter.rewrite_url("github.com/steinwurf/gtest.git")
    assert r == "https://github.com/steinwurf/gtest.git"


def test_git_url_rewriter_git_at():

    parser = GitUrlParser()
    rewriter = GitUrlRewriter(parser=parser, rewrite_protocol="git@")

    r = rewriter.rewrite_url("github.com/steinwurf/gtest.git")
    assert r == "git@github.com:steinwurf/gtest.git"


def test_git_url_rewriter_git():

    parser = GitUrlParser()
    rewriter = GitUrlRewriter(parser=parser, rewrite_protocol="git://")

    r = rewriter.rewrite_url("github.com/steinwurf/gtest.git")
    assert r == "git://github.com/steinwurf/gtest.git"


def test_git_url_rewriter_ssh_git_at():

    parser = GitUrlParser()
    rewriter = GitUrlRewriter(parser=parser, rewrite_protocol="ssh://git@")

    r = rewriter.rewrite_url("github.com/steinwurf/rely-python.git")
    assert r == "git@github.com:steinwurf/rely-python.git"


def test_git_url_rewriter_custom():

    parser = GitUrlParser()
    rewriter = GitUrlRewriter(
        parser=parser,
        rewrite_protocol="git+https://TOKEN:x-oauth-basic@{host}/{path}.git",
    )

    r = rewriter.rewrite_url("github.com/steinwurf/gtest.git")
    assert r == "git+https://TOKEN:x-oauth-basic@github.com/steinwurf/gtest.git"


def test_git_url_rewriter_no_rewrite():

    parser = GitUrlParser()
    rewriter = GitUrlRewriter(parser=parser, rewrite_protocol="git@")

    r = rewriter.rewrite_url("https://github.com/steinwurf/gtest.git")
    assert r == "https://github.com/steinwurf/gtest.git"
