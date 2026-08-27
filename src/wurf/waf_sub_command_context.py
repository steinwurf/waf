#! /usr/bin/env python
# encoding: utf-8

from waflib import Context

from .sub_command import sub_commands


def create_sub_command_context(sub_command):
    """Create the context making a sub command show up in the list of waf
    commands. Waf builds that list from the registered contexts.

    A sub command is taken out of the arguments before waf builds the list of
    commands to run, so the context is never executed.

    :param sub_command: The SubCommand class to create the context for
    :return: The created context class
    """
    name = f"{sub_command.command}_{sub_command.name}".title().replace("_", "")

    return type(
        f"Waf{name}Context",
        (Context.Context,),
        {
            "cmd": f"{sub_command.command} {sub_command.name}",
            "fun": sub_command.command,
            "__doc__": sub_command.help,
        },
    )


for _sub_command in sub_commands():
    create_sub_command_context(sub_command=_sub_command)
