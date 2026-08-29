import semver

from wurf.semver_selector import SemverSelector


def test_semver_selector():
    selector = SemverSelector(semver=semver)

    tags = [
        "2.3.4",
        "1.0.0",
        "1.3.5",
        "1.0.1",
        "2.0.0",
        "1.1.2",
        "1.1.1",
        "3.0.0",
        "3.0.0-lts.0",
        "3.0.0-lts.1",
        "backups/3.1.0-lts.0",  # Do not match non-toplevel tags.
        "4.0.0",
        "v4.0.1",
        "5.0.0",
        "5.1",
    ]

    # Select latest tag for major version 1
    assert selector.select_tag(major=1, tags=tags) == "1.3.5"

    # Select latest tag for major version 2
    assert selector.select_tag(major=2, tags=tags) == "2.3.4"

    # Select latest tag for major version 3 (LTS tags should be ignored)
    assert selector.select_tag(major=3, tags=tags) == "3.0.0"

    # Select latest tag for major version 4 (v prefix should be ignored)
    assert selector.select_tag(major=4, tags=tags) == "v4.0.1"

    # Select latest tag for major version 5 (missing minor should be ignored)
    assert selector.select_tag(major=5, tags=tags) == "5.1"
