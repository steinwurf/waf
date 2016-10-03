import pytest
import mock

from wurf_source_parser_action import WurfSourceParserAction

def test_wurf_source_parser_action():

    sources = [{"type":"git_commit", "url":"gitrepo.git", "commit": "sha1"},
               {"type":"git_semver", "url":"gitrepo1.git", "major": 1}]

    def parse_git_commit(dependency, url, commit):
        assert(url == "gitrepo.git")
        assert(commit == "sha1")

    def parse_git_semver(dependency, url, major):
        assert(url == "gitrepo1.git")
        assert(major == 1)

    actions = {'git_commit': parse_git_commit, 'git_semver': parse_git_semver}

    parser = WurfSourceParserAction(source_actions=actions)

    dependency = parser(dependency=mock.Mock(), sources=sources)

def test_wurf_source_parser_action_no_type():

    sources = [{"url":"gitrepo.git", "commit": "sha1"}]

    parser = WurfSourceParserAction(source_actions=None)

    with pytest.raises(Exception):
        parser(dependency=mock.Mock(), sources=sources)
