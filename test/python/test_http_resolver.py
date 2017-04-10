import pytest
import mock
import vcr
try:
    from urllib.request import urlopen, Request
except ImportError:
    from urllib2 import urlopen, Request


def test_vcr():
    pass
