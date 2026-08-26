#! /usr/bin/env python
# encoding: utf-8


# The waf command running the dependency resolution
RESOLVE_COMMAND = "resolve"


class SubCommand(object):
    """Base class for the sub commands of the resolve command.

    A sub command is used as "./waf resolve <name> [argument ...]" and changes
    how the dependencies are resolved.

    A sub class defines the name used on the command-line, the one line help
    shown in the list of waf commands, and the description shown with the
    resolve options.
    """

    # The name used on the command-line
    name = None

    # One line help, shown in the list of waf commands
    help = None

    # Description of the sub command, shown with the resolve options
    description = None

    def __init__(self, arguments):
        """Construct an instance.

        :param arguments: The arguments following the sub command as a list
        """
        self.arguments = arguments


class UpgradeSubCommand(SubCommand):
    name = "upgrade"

    help = "upgrades the given dependencies, and the dependencies they pull in"

    description = (
        "The command 'resolve upgrade [dependency ...]' upgrades the given "
        "dependencies, and the dependencies they pull in, to their newest "
        "version. Without any names all dependencies are upgraded."
    )


def sub_commands():
    """:return: The available sub commands as a list of SubCommand classes."""
    return [UpgradeSubCommand]


def parse(args):
    """Take the sub command out of the command-line arguments.

    Waf treats every argument which is not an option as a command, so the sub
    command and its arguments must be removed before waf parses the arguments.

    :param args: The command-line arguments as a list
    :return: A (sub command, arguments) tuple, where sub command is a
        SubCommand instance or None if no sub command was used, and arguments
        are the remaining command-line arguments.
    """
    available = {sub_command.name: sub_command for sub_command in sub_commands()}

    for index, arg in enumerate(args):
        if arg != RESOLVE_COMMAND:
            continue

        command = index + 1

        if command >= len(args) or args[command] not in available:
            continue

        # The arguments of the sub command follow it and stop at the first
        # option
        start = command + 1
        end = start

        while end < len(args) and not args[end].startswith("-"):
            end += 1

        sub_command = available[args[command]](arguments=args[start:end])

        return sub_command, args[:command] + args[end:]

    return None, args
