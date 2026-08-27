from wurf.sub_command import UpgradeSubCommand
from wurf.sub_command import parse
from wurf.sub_command import sub_commands


def test_upgrade_sub_command():
    assert UpgradeSubCommand.command == "resolve"
    assert UpgradeSubCommand.name == "upgrade"

    assert sub_commands(command="resolve") == [UpgradeSubCommand]
    assert sub_commands(command="build") == []


def test_parse_without_sub_command():
    assert parse(args=["configure", "--lock_versions"]) == (
        None,
        ["configure", "--lock_versions"],
    )

    # An unknown name is left alone, waf reports it as an unknown command
    sub_command, args = parse(args=["resolve", "downgrade"])

    assert sub_command is None
    assert args == ["resolve", "downgrade"]

    # A sub command only belongs to the command it extends
    sub_command, args = parse(args=["build", "upgrade"])

    assert sub_command is None
    assert args == ["build", "upgrade"]


def test_parse_sub_command():
    sub_command, args = parse(args=["resolve", "upgrade", "foo", "bar"])

    assert isinstance(sub_command, UpgradeSubCommand)
    assert sub_command.arguments == ["foo", "bar"]

    # The sub command and its arguments are removed, the resolve command is
    # kept as waf must still run it
    assert args == ["resolve"]


def test_parse_sub_command_arguments_stop_at_option():
    sub_command, args = parse(
        args=["configure", "resolve", "upgrade", "foo", "-v", "bar"]
    )

    assert sub_command.arguments == ["foo"]
    assert args == ["configure", "resolve", "-v", "bar"]
