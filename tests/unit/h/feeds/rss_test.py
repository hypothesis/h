import datetime
from unittest import mock

import pytest

from h import models
from h.feeds import rss


def _annotation_url():
    """
    Return a mock annotation_url() function.

    It just returns a hard-coded URL, enough to make the code that calls this
    function not crash.

    """
    return mock.Mock(return_value="https://hypothes.is/a/id")


def _annotation(**kwargs):
    args = {
        "userid": "acct:janebloggs@hypothes.is",
        "target_selectors": [],
        "created": datetime.datetime.utcnow(),
        "updated": datetime.datetime.utcnow(),
        "document": models.Document(),
    }
    args.update(**kwargs)
    return models.Annotation(**args)


@pytest.mark.parametrize(
    "userid,name",
    (
        ("acct:username@hypothes.is", "username"),
        ("malformed", "malformed"),
    ),
)
def test_feed_from_annotations_item_author(userid, name):
    """Feed items should include the annotation's author."""
    annotation = _annotation(userid=userid)

    feed = rss.feed_from_annotations(
        [annotation], _annotation_url(), mock.Mock(), "", "", ""
    )

    assert feed["entries"][0]["author"]["name"] == name


def test_feed_annotations_pubDate():
    """It should render the pubDates of annotations correctly."""
    ann = _annotation(
        created=datetime.datetime(
            year=2015, month=3, day=11, hour=10, minute=43, second=54
        )
    )

    feed = rss.feed_from_annotations([ann], _annotation_url(), mock.Mock(), "", "", "")

    assert feed["entries"][0]["pubDate"] == "Wed, 11 Mar 2015 10:43:54 -0000"


def test_feed_from_annotations_html_links(factories):
    """Items should include links to the annotations' HTML pages."""
    annotation_url = _annotation_url()

    feed = rss.feed_from_annotations(
        [factories.Annotation()], annotation_url, mock.Mock(), "", "", ""
    )

    item = feed["entries"][0]
    assert item["link"] == annotation_url.return_value


def test_feed_from_annotations_item_titles(factories):
    """Feed items should include the annotation's document's title."""
    document = factories.Document(title="Hello, World")
    annotation = factories.Annotation(document=document)

    feed = rss.feed_from_annotations(
        [annotation], _annotation_url(), mock.Mock(), "", "", ""
    )

    assert feed["entries"][0]["title"] == annotation.document.title


def test_feed_from_annotations_item_descriptions(factories):
    """Feed items should include a description of the annotation."""
    with mock.patch(
        "h.feeds.rss.presenters.AnnotationHTMLPresenter.description",
        new_callable=mock.PropertyMock,
    ) as description:
        feed = rss.feed_from_annotations(
            [factories.Annotation()], _annotation_url(), mock.Mock(), "", "", ""
        )

        assert feed["entries"][0]["description"] == (description.return_value)


def test_feed_from_annotations_item_guid(factories):
    """Feed items should use the annotation's HTML URL as their GUID."""
    annotation = factories.Annotation(
        created=datetime.datetime(year=2015, month=3, day=11)
    )

    feed = rss.feed_from_annotations(
        [annotation], _annotation_url(), mock.Mock(), "", "", ""
    )

    assert feed["entries"][0]["guid"] == ("tag:hypothes.is,2015-09:" + annotation.id)


def test_feed_from_annotations_title():
    """The feed should use the given title for its title field."""
    feed = rss.feed_from_annotations(
        [], _annotation_url(), mock.Mock(), "", "Hypothesis Stream", ""
    )

    assert feed["title"] == "Hypothesis Stream"


def test_feed_from_annotations_link():
    """The feed should use the given html_url for its html_url field."""
    feed = rss.feed_from_annotations(
        [], _annotation_url(), mock.Mock(), "http://Hypothes.is/stream", "", ""
    )

    assert feed["html_url"] == "http://Hypothes.is/stream"


def test_feed_from_annotations_description():
    """The feed should use the given description for its description field."""
    feed = rss.feed_from_annotations(
        [], _annotation_url(), mock.Mock(), "", "", "The Web. Annotated"
    )

    assert feed["description"] == "The Web. Annotated"


def test_feed_from_annotations_with_0_annotations():
    """If there are no annotations it should return [] for entries."""
    feed = rss.feed_from_annotations([], _annotation_url(), mock.Mock(), "", "", "")

    assert feed["entries"] == []


def test_feed_from_annotations_with_1_annotation(factories):
    """If there's 1 annotation it should return 1 entry."""
    feed = rss.feed_from_annotations(
        [factories.Annotation()], _annotation_url(), mock.Mock(), "", "", ""
    )

    assert len(feed["entries"]) == 1


def test_feed_from_annotations_with_3_annotations(factories):
    """If there are 3 annotations it should return 3 entries."""
    annotations = [
        factories.Annotation(),
        factories.Annotation(),
        factories.Annotation(),
    ]

    feed = rss.feed_from_annotations(
        annotations, _annotation_url(), mock.Mock(), "", "", ""
    )

    assert len(feed["entries"]) == 3


def test_feed_from_annotations_pubDate():
    """The pubDate should be the updated time of the most recent annotation."""
    annotations = [
        _annotation(
            updated=datetime.datetime(
                year=2015,
                month=3,
                day=11,
                hour=10,
                minute=45,
                second=54,
                microsecond=537626,
            )
        ),
        _annotation(
            updated=datetime.datetime(
                year=2015,
                month=2,
                day=11,
                hour=10,
                minute=43,
                second=54,
                microsecond=537626,
            )
        ),
        _annotation(
            updated=datetime.datetime(
                year=2015,
                month=1,
                day=11,
                hour=10,
                minute=43,
                second=54,
                microsecond=537626,
            )
        ),
    ]

    feed = rss.feed_from_annotations(
        annotations, _annotation_url(), mock.Mock(), "", "", ""
    )

    assert feed["pubDate"] == "Wed, 11 Mar 2015 10:45:54 -0000"
