#! /usr/bin/env python
# encoding: utf-8


class SubCommand(object):
    """Base class for the sub commands.

    A sub command is used as "./waf <command> <name> [argument ...]" and
    changes what the command it belongs to does.

    A sub class defines the command it extends, the name used on the
    command-line, the one line help shown in the list of waf commands, and the
    description shown with the options of the command.
    """

    # The waf command the sub command belongs to
    command = None

    # The name used on the command-line
    name = None

    # One line help, shown in the list of waf commands
    help = None

    # Description of the sub command, shown with the options of the command
    description = None

    def __init__(self, arguments):
        """Construct an instance.

        :param arguments: The arguments following the sub command as a list
        """
        self.arguments = arguments


class UpgradeSubCommand(SubCommand):
    command = "resolve"

    name = "upgrade"

    help = "upgrades the given dependencies, and the dependencies they pull in"

    description = (
        "The command 'resolve upgrade [dependency ...]' upgrades the given "
        "dependencies, and the dependencies they pull in, to their newest "
        "version. Without any names all dependencies are upgraded."
    )


def sub_commands(command=None):
    """Return the available sub commands.

    :param command: Only return the sub commands of this waf command, as a
        string. All sub commands are returned if None.
    :return: The sub commands as a list of SubCommand classes
    """
    available = [UpgradeSubCommand]

    if command is None:
        return available

    return [s for s in available if s.command == command]


def parse(args):
    """Take the sub command out of the command-line arguments.

    Waf treats every argument which is not an option as a command, so the sub
    command and its arguments must be removed before waf parses the arguments.

    :param args: The command-line arguments as a list
    :return: A (sub command, arguments) tuple, where sub command is a
        SubCommand instance or None if no sub command was used, and arguments
        are the remaining command-line arguments.
    """
    available = {(s.command, s.name): s for s in sub_commands()}

    for index, arg in enumerate(args):
        name = index + 1

        if name >= len(args):
            break

        sub_command = available.get((arg, args[name]), None)

        if sub_command is None:
            continue

        # The arguments of the sub command follow it and stop at the first
        # option
        start = name + 1
        end = start

        while end < len(args) and not args[end].startswith("-"):
            end += 1

        # The command itself is kept, waf must still run it
        return sub_command(arguments=args[start:end]), args[:name] + args[end:]

    return None, args
