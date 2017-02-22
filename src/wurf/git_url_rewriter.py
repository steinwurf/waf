#! /usr/bin/env python
# encoding: utf-8



class GitUrlRewriter(object):

    git_protocols = {
        'https://': 'https://{}/{}.git',
        'http://': 'http://{}/{}.git',
        'git@': 'git@{}:{}.git',
        'git://': 'git://{}/{}.git'
    }

    def __init__(self, parser, rewrite_protocol):
        self.parser = parser
        self.format_url = GitUrlRewriter.git_protocols[rewrite_protocol]

    def rewrite_url(self, url):

        u = self.parser.parse(url)
        return self.format_url.format(u.host, u.path)
