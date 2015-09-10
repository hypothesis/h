import datetime
import mock

from h.test import factories
from h.feeds import util


def test_tag_uri_for_annotation():
    """Entry IDs should be tag URIs based on domain, day and annotation ID."""
    annotation = factories.Annotation(
        id="12345",
        created=datetime.datetime(year=2015, month=3, day=19).isoformat())

    tag_uri = util.tag_uri_for_annotation(
        annotation,
        annotation_url=mock.Mock(return_value="http://example.com/a/12345"))

    assert tag_uri == "tag:example.com,2015-09:12345"
