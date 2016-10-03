import pytest

from wurf_dependency_parser import WurfDependencyParser

def test_wurf_dependency_parser():

    waf = '{"name":"waf", "patches": ["patches/patch01.patch", \
            "patches/patch02.patch"], "optional":true, \
            "sources":[{"url":"gitrepo.git", "commit": "sha1"}]}'

    def parse_sources(dependency, sources):
        expect = [{"url":"gitrepo.git", "commit": "sha1"}]
        assert(expect == sources)

    def parse_optional(dependency, optional):
        expect = True
        assert(expect == optional)

    def parse_patches(dependency, patches):
        expect = ["patches/patch01.patch", "patches/patch02.patch"]
        assert(expect == patches)

    def dependency_factory(name):
        assert(name == "waf")

    actions = {'sources': parse_sources, 'optional': parse_optional,
               'patches': parse_patches}

    parser = WurfDependencyParser(parse_actions=actions,
        dependency_factory=dependency_factory)

    dependency = parser.parse_json(waf)

def test_wurf_dependency_parser_no_name():

    noname = '{"optional": true, "patches": ["patches/patch01.patch", \
               "patches/patch02.patch"], "sources": [{"url":"gitrepo.git"}]}'

    parser = WurfDependencyParser(parse_actions=None, dependency_factory=None)

    with pytest.raises(Exception):
        parser.parse_json(noname)
