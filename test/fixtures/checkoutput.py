import fnmatch

class CheckOutput:
    """Stores the output after running a command typically standard
    output or standard error.

    Attributes:

    :output: List of strings representing the output (split by newlines)

    """

    def __init__(self, output):
        """ Creates a new CheckOutput object

        :param output: String representing the output
        """
        self.output = output.splitlines()

    def match(self, pattern):
        """ Matches the lines in the output with the pattern. The match
        pattern can contain basic wildcards, see
        https://docs.python.org/2/library/fnmatch.html

        For convenience:

            +-----------------------------------------+
            |Pattern|Meaning                          |
            +-----------------------------------------+
            |*      |matches everything               |
            +-----------------------------------------+
            |?      |matches any single character     |
            +-----------------------------------------+
            |[seq]  |matches any character in seq     |
            +-----------------------------------------+
            |[!seq] |matches any character not in seq |
            +-----------------------------------------+

        Simple example:

            out.match('*success*')

        Will return True if one or more of the lines in out.output contains
        the word success.

        :param pattern: Pattern to search for in the list of output string

        :return: True if the pattern is found in one or more of the output
                 lines.

        """
        match_lines = fnmatch.filter(self.output, pattern)
        return len(match_lines) > 0

    def __str__(self):
        """
        Generate a single string representation of the output.

        :return: A string representing the output.
        """
        return '\n'.join(self.output)

    def __repr__(self):
        """
        Generate a string representation of this object for pretty prints.

        :return: A string representing the output.
        """
        return 'CheckOutput: "{}"'.format('\n'.join(self.output))
