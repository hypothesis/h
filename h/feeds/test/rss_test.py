import datetime

import mock

from h.test import factories
from h.feeds import rss


def _annotation_url():
    """Return a mock annotation_url() function.

    It just returns a hard-coded URL, enough to make the code that calls this
    function not crash.

    """
    return mock.Mock(return_value='https://hypothes.is/a/id')


def test_feed_from_annotations_item_author():
    """Feed items should include the annotation's author."""
    annotation = factories.Annotation(username="janebloggs")

    feed = rss.feed_from_annotations(
        [annotation], _annotation_url(), mock.Mock(), '', '', '')

    assert feed['entries'][0]['author'] == {'name': 'janebloggs'}


def test_feed_from_annotations_pubDate():
    """It should render the pubDates of annotations correctly."""
    annotation = factories.Annotation(
        created=datetime.datetime(year=2015, month=3, day=11, hour=10,
                                  minute=43, seconds=54).isoformat())

    feed = rss.feed_from_annotations(
        [annotation], _annotation_url(), mock.Mock(), '', '', '')

    assert feed['entries'][0]['pubDate'] == 'Wed, 11 Mar 2015 10:43:54 +0000'


def test_feed_from_annotations_html_links():
    """Items should include links to the annotations' HTML pages."""
    annotation_url = _annotation_url()

    feed = rss.feed_from_annotations(
        [factories.Annotation()], annotation_url, mock.Mock(), '', '', '')

    item = feed['entries'][0]
    assert item['link'] == annotation_url.return_value


def test_feed_from_annotations_item_titles():
    """Feed items should include the annotation's document's title."""
    annotation = factories.Annotation()

    feed = rss.feed_from_annotations(
        [annotation], _annotation_url(), mock.Mock(), '', '', '')

    assert feed['entries'][0]['title'] == annotation['document']['title']


def test_feed_from_annotations_item_descriptions():
    """Feed items should include a description of the annotation."""
    with mock.patch(
            "h.feeds.rss.presenters.AnnotationHTMLPresenter.description",
            new_callable=mock.PropertyMock) as description:
        feed = rss.feed_from_annotations(
            [factories.Annotation()], _annotation_url(), mock.Mock(), '', '', '')

        assert feed['entries'][0]['description'] == (
            description.return_value)


def test_feed_from_annotations_item_guid():
    """Feed items should use the annotation's HTML URL as their GUID."""
    feed = rss.feed_from_annotations(
        [factories.Annotation(
            id='id',
            created=datetime.datetime(year=2015, month=3, day=11).isoformat())
         ], _annotation_url(), mock.Mock(), '', '', '')

    assert feed['entries'][0]['guid'] == 'tag:hypothes.is,2015-09:id'


def test_feed_from_annotations_title():
    """The feed should use the given title for its title field."""
    feed = rss.feed_from_annotations(
        [], _annotation_url(), mock.Mock(), '', 'Hypothesis Stream', '')

    assert feed['title'] == 'Hypothesis Stream'


def test_feed_from_annotations_link():
    """The feed should use the given html_url for its html_url field."""
    feed = rss.feed_from_annotations(
        [], _annotation_url(), mock.Mock(), 'http://Hypothes.is/stream', '',
        '')

    assert feed['html_url'] == 'http://Hypothes.is/stream'


def test_feed_from_annotations_description():
    """The feed should use the given description for its description field."""
    feed = rss.feed_from_annotations(
        [], _annotation_url(), mock.Mock(), '', '', 'The Web. Annotated')

    assert feed['description'] == 'The Web. Annotated'


def test_feed_from_annotations_with_0_annotations():
    """If there are no annotations it should return [] for entries."""
    feed = rss.feed_from_annotations(
        [], _annotation_url(), mock.Mock(), '', '', '')

    assert feed['entries'] == []


def test_feed_from_annotations_with_1_annotation():
    """If there's 1 annotation it should return 1 entry."""
    feed = rss.feed_from_annotations(
        [factories.Annotation()], _annotation_url(), mock.Mock(), '', '', '')

    assert len(feed['entries']) == 1


def test_feed_from_annotations_with_3_annotations():
    """If there are 3 annotations it should return 3 entries."""
    annotations = [factories.Annotation(), factories.Annotation(),
                   factories.Annotation()]

    feed = rss.feed_from_annotations(
        annotations, _annotation_url(), mock.Mock(), '', '', '')

    assert len(feed['entries']) == 3


def test_feed_from_annotations_pubDate():
    """The pubDate should be the updated time of the most recent annotation."""
    annotations = [
        factories.Annotation(updated='2015-03-11T10:45:54.537626+00:00'),
        factories.Annotation(updated='2015-02-11T10:43:54.537626+00:00'),
        factories.Annotation(updated='2015-01-11T10:43:54.537626+00:00')
    ]

    feed = rss.feed_from_annotations(
        annotations, _annotation_url(), mock.Mock(), '', '', '')

    assert feed['pubDate'] == 'Wed, 11 Mar 2015 10:45:54 UTC'
