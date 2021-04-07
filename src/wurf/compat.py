#! /usr/bin/env python
# encoding: utf-8

import sys
import codecs

IS_PY2 = sys.version_info[0] == 2


def check_locale_python3():
    """ Python 3 depends on the locale to be specified to properly handle
    unicode characters.

    You can read about the problem in the Click project documentation:
    http://click.pocoo.org/5/python3/#python-3-surrogate-handling

    tl;dr Python 3 relies on the locale of the computer where the
    interpreter is running to handled non-ascii characters. If the
    locale is missing or incorrectly specified it will raise an
    UnicodeError.

    We cannot do much about this but to warn the user, that he/she should
    configure their environment.
    """

    # Same approach as:
    # https://github.com/pallets/click/blob/8d9dd4/click/_unicodefun.py#L50

    if IS_PY2:
        return

    try:
        import locale
        fs_enc = codecs.lookup(locale.getpreferredencoding()).name
    except LookupError:
        fs_enc = 'ascii'

    if fs_enc == 'ascii':
        raise RuntimeError(
            'We will abort further execution because Python 3 '
            'was configured to use ASCII as encoding for the '
            'environment. Consult e.g. http://click.pocoo.org/python3/'
            'for mitigation steps.')
    else:
        return
