import pytest

from wurf.mandatory_options import MandatoryOptions


def test_mandatory_options():
    class opt(object):
        def name_none(self):
            return None

        def name(self, world):
            return "hello " + world

    options = MandatoryOptions(options=opt())

    with pytest.raises(RuntimeError):
        options.name_none()

    assert options.name("world") == "hello world"
