import json

from wurf_dependency import WurfDependency2

class WurfDependencyParser(object):

    def __init__(self, parse_actions):
        self.parse_actions = parse_actions

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

        dependency = WurfDependency2(name)

        for key, value  in data.items():
            action = self.parse_actions[key]

            # Take the key and pass it as a keyword argument to the action
            action(dependency=dependency, **{key: value})

        return dependency
