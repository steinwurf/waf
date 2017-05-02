import pytest
import mock

from wurf.tag_database import TagDatabase

@pytest.mark.networktest
def test_tag_database():

    ctx = mock.Mock()

    db = TagDatabase(ctx=ctx)

    # Test that we can retrive the tags for a common Steinwurf project
    tags = db.project_tags(project_name='waf-tools')

    # Check some unique tags for waf-tools
    assert len(tags) > 0, "mock ctx %s" % ctx
    assert '2.53.1' in tags
    assert '3.19.0' in tags
