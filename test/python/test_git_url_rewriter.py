from wurf.git_url_parser import GitUrlParser
from wurf.git_url_rewriter import GitUrlRewriter


def test_git_url_rewriter_https():

    parser = GitUrlParser()
    rewriter = GitUrlRewriter(parser=parser, rewrite_protocol = 'https://')

    r = rewriter.rewrite_url('github.com/steinwurf/gtest.git')
    assert r == 'https://github.com/steinwurf/gtest.git'


def test_git_url_rewriter_git_at():

    parser = GitUrlParser()
    rewriter = GitUrlRewriter(parser=parser, rewrite_protocol = 'git@')

    r = rewriter.rewrite_url('github.com/steinwurf/gtest.git')
    assert r == 'git@github.com:steinwurf/gtest.git'


def test_git_url_rewriter_git():

    parser = GitUrlParser()
    rewriter = GitUrlRewriter(parser=parser, rewrite_protocol = 'git://')

    r = rewriter.rewrite_url('github.com/steinwurf/gtest.git')
    assert r == 'git://github.com/steinwurf/gtest.git'
