#! /usr/bin/env python
# encoding: utf-8

git_protocols = {
    'https://': 'https://{}/{}.git',
    'git@': 'git@{}:{}.git',
    'git://': 'git://{}/{}.git'
}

class GitUrlRewriter(object):

    def __init__(self, parser, preferred_protocol = 'https://'):
        self.parser = parser
        self.format_url = git_protocols[preferred_protocol]

    def rewrite_url(self, url):

        u = self.parser.parse(url)
        return self.format_url.format(u.host, u.path)
