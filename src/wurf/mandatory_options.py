#! /usr/bin/env python
# encoding: utf-8


class MandatoryOptions(object):
    """Options wrapper that ensures that an option has a value.

    This is useful in parts of the code where it is know that an option
    must have a value.
    """

    def __init__(self, options):
        """Construct a new instance.

        :param options: An Options instance.
        """
        self.options = options

    def __getattr__(self, name):
        """Access one of the options.

        :param name: The option name.
        """

        call = getattr(self.options, name)

        # Wrap the option access function with a function which
        # checks that the arguement is not None

        def require(*args, **kwargs):
            value = call(*args, **kwargs)

            if value is None:
                raise RuntimeError(
                    'Mandatory option "{}" was set to "None"'.format(name)
                )
            return value

        return require
