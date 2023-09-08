#! /usr/bin/env python
# encoding: utf-8


class WurfError(Exception):
    """Basic exception for errors raised by wurf tools"""

    def __init__(self, *args):
        super(WurfError, self).__init__(*args)

    def __str__(self):
        return "\n".join(map(str, self.args))


class CmdAndLogError(WurfError):
    def __init__(self, error):
        self.error = error
        msg = str(error)
        if hasattr(error, "stdout") and len(error.stdout):
            msg += f"\nstdout:\n{error.stdout}"
        if hasattr(error, "stderr") and len(error.stderr):
            msg += f"\nstderr:\n{error.stderr}"
        super(CmdAndLogError, self).__init__(msg)


class DependencyError(WurfError):
    def __init__(self, msg, dependency):
        super(DependencyError, self).__init__(msg, help_message(dependency))


class TopLevelError(WurfError):
    """
    Top-level error that also displays error messages that might have
    occurred previously when resolving this dependency
    """

    def __init__(self, msg, dependency):
        if isinstance(dependency.error_messages, list) and len(
            dependency.error_messages
        ):
            msg += "\n"
            msg += "\n".join(dependency.error_messages)
        super(TopLevelError, self).__init__(msg, help_message(dependency))


def help_message(dependency):
    text = f'ERROR: the "{dependency.name}" dependency is not available.'
    if dependency.resolver == "git":
        steinwurf_sources = [
            "https://" + s for s in dependency.sources if "steinwurf" in s
        ]
        if len(steinwurf_sources):
            text += (
                "\nPlease check that you have a valid Steinwurf "
                "license and you can access the repository at: "
                f"{map(str, steinwurf_sources)}"
            )
    return text


class RelativeSymlinkError(WurfError):
    def __init__(self, *args):
        super(RelativeSymlinkError, self).__init__(
            "Relative symlinks are not supported on this platform", *args
        )
