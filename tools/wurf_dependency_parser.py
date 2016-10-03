import json

class WurfDependencyParser(object):
    """
    Creates a dependency and based on a JSON/dict object calls actions to
    initialize the dependency.

    Take the following JSON:

        waf = '{"name":"waf", "patches": ["patches/patch01.patch",
                "patches/patch02.patch"], "optional":true,
                "sources":[{"url":"gitrepo.git", "commit": "sha1"}]}'

    The dependency parser will for each top-level key:

         patches, optional, sources

    Call a parse action to initialize the dependency. A parse action is a
    callable object which takes as first argument the dependency and as second
    argument the value passed for the specific key.

    Example:

        def parse_optional(dependency, optional):
            pass

    Is a valid parse action for the "optional" key.
    """

    def __init__(self, parse_actions, dependency_factory):
        self.parse_actions = parse_actions
        self.dependency_factory = dependency_factory

    def parse_json(self, data):

        data = json.loads(data)
        return self.parse_dict(data)

    def parse_dict(self, data):

        # The name attribute MUST exist and is sometimes required for resolvers
        # that provide options here we fetch the name.
        name = data['name']

        # Delete the name in the dependency data such that we do
        # not try to find a parse action for it..
        del data['name']

        dependency = self.dependency_factory(name=name)

        for key, value  in data.items():
            action = self.parse_actions[key]
            action(dependency, value)

        return dependency
