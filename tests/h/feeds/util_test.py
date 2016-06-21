import datetime

import mock

from h.feeds import util

from ...common import factories


def test_tag_uri_for_annotation():
    """Entry IDs should be tag URIs based on domain, day and annotation ID."""
    annotation = factories.Annotation(
        created=datetime.datetime(year=2015, month=3, day=19))

    tag_uri = util.tag_uri_for_annotation(
        annotation,
        annotation_url=mock.Mock(return_value="http://example.com/a/12345"))

    assert tag_uri == "tag:example.com,2015-09:" + annotation.id
