from wurf.tag_selector import select_newest_tag
from wurf.tag_selector import split_tag


def test_split_tag():
    assert split_tag("1.2.3") == ("", (1, 2, 3))
    assert split_tag("v1.2.3") == ("v", (1, 2, 3))
    assert split_tag("waf-2.0.26") == ("waf-", (2, 0, 26))
    assert split_tag("1.3.3.7") == ("", (1, 3, 3, 7))
    assert split_tag("master") is None


def test_select_newest_tag():
    tags = ["1.0.0", "1.2.0", "2.0.0", "v3.0.0", "master"]

    assert select_newest_tag(current="1.0.0", tags=tags) == "2.0.0"
    assert select_newest_tag(current="1.2.0", tags=tags) == "2.0.0"

    # The newest tag is already used
    assert select_newest_tag(current="2.0.0", tags=tags) is None

    # Only tags with the same prefix are considered
    assert select_newest_tag(current="v1.0.0", tags=tags) == "v3.0.0"

    # A branch or a commit id cannot be upgraded
    assert select_newest_tag(current="master", tags=tags) is None
    assert select_newest_tag(current="someh4sh", tags=tags) is None


def test_select_newest_tag_ignores_pre_release():
    tags = ["1.0.0", "2.0.0-rc1"]

    assert select_newest_tag(current="1.0.0", tags=tags) is None
