# -*- coding: utf-8 -*-
# pylint: disable=protected-access
"""Unit tests for h/atom.py."""
from __future__ import unicode_literals
from datetime import datetime
import mock

from h import models
from h.feeds import atom


def _annotation(**kwargs):
    args = {
        "userid": "acct:janebloggs@hypothes.is",
        "created": datetime.utcnow(),
        "updated": datetime.utcnow(),
        "target_selectors": [],
        "document": models.Document(),
    }
    args.update(kwargs)
    return models.Annotation(**args)


def test_feed_id():
    feed = atom.feed_from_annotations([], "atom_url", mock.Mock())

    assert feed["id"] == "atom_url"


def test_feed_title():
    feed = atom.feed_from_annotations([], mock.Mock(), mock.Mock(), title="foo")

    assert feed["title"] == "foo"


def test_feed_subtitle():
    feed = atom.feed_from_annotations([], mock.Mock(), mock.Mock(), subtitle="bar")

    assert feed["subtitle"] == "bar"


@mock.patch("h.feeds.atom._feed_entry_from_annotation")
def test_feed_contains_entries(_feed_entry_from_annotation, factories):
    """The feed should contain an entry for each annotation."""
    annotations = [
        factories.Annotation(),
        factories.Annotation(),
        factories.Annotation(),
    ]
    annotations_url_function = mock.Mock()
    annotations_api_url_function = mock.Mock()
    entries = [
        "feed entry for annotation 1",
        "feed entry for annotation 2",
        "feed entry for annotation 3",
    ]

    def pop(*args, **kwargs):
        return entries.pop(0)

    _feed_entry_from_annotation.side_effect = pop

    feed = atom.feed_from_annotations(
        annotations, annotations_url_function, annotations_api_url_function
    )

    assert feed["entries"] == [
        "feed entry for annotation 1",
        "feed entry for annotation 2",
        "feed entry for annotation 3",
    ]


def test_atom_url_link():
    """The feed should contain a link to its Atom URL."""
    feed = atom.feed_from_annotations([], "atom_url", mock.Mock())

    assert feed["links"][0] == {
        "rel": "self",
        "type": "application/atom+xml",
        "href": "atom_url",
    }


def test_html_url_link():
    """The feed should contain a link to its corresponding HTML page."""
    feed = atom.feed_from_annotations([], mock.Mock(), mock.Mock(), html_url="html_url")

    assert feed["links"][1] == {
        "rel": "alternate",
        "type": "text/html",
        "href": "html_url",
    }


@mock.patch("h.feeds.util")
def test_entry_id(util, factories):
    """The ids of feed entries should come from tag_uri_for_annotation()."""
    annotation = factories.Annotation()

    def annotation_url(ann):
        return "annotation url"

    feed = atom.feed_from_annotations([annotation], "atom_url", annotation_url)

    util.tag_uri_for_annotation.assert_called_once_with(annotation, annotation_url)
    assert feed["entries"][0]["id"] == util.tag_uri_for_annotation.return_value


def test_entry_author(factories):
    """The authors of entries should come from the annotation usernames."""
    annotation = factories.Annotation(userid="acct:nobu@hypothes.is")

    feed = atom.feed_from_annotations(
        [annotation], "atom_url", lambda annotation: "annotation url"
    )

    assert feed["entries"][0]["author"]["name"] == "nobu"


def test_entry_title(factories):
    """The titles of feed entries should come from annotation.title."""
    with mock.patch(
        "h.feeds.atom.presenters.AnnotationHTMLPresenter.title",
        new_callable=mock.PropertyMock,
    ) as mock_title:
        annotation = factories.Annotation()

        feed = atom.feed_from_annotations(
            [annotation], "atom_url", lambda annotation: "annotation url"
        )

        mock_title.assert_called_once_with()
        assert feed["entries"][0]["title"] == mock_title.return_value


def test_entry_updated():
    """The updated times of entries should come from the annotations."""
    annotation = _annotation(
        updated=datetime(
            year=2016,
            month=2,
            day=29,
            hour=16,
            minute=39,
            second=12,
            microsecond=537626,
        )
    )

    feed = atom.feed_from_annotations(
        [annotation], "atom_url", lambda annotation: "annotation url"
    )

    assert feed["entries"][0]["updated"] == "2016-02-29T16:39:12.537626+00:00"


def test_entry_published():
    """The published times of entries should come from the annotations."""
    annotation = _annotation(
        created=datetime(
            year=2016,
            month=5,
            day=31,
            hour=12,
            minute=15,
            second=45,
            microsecond=537626,
        )
    )

    feed = atom.feed_from_annotations(
        [annotation], "atom_url", lambda annotation: "annotation url"
    )

    assert feed["entries"][0]["published"] == "2016-05-31T12:15:45.537626+00:00"


def test_entry_content(factories):
    """The contents of entries come from annotation.description."""
    with mock.patch(
        "h.feeds.atom.presenters.AnnotationHTMLPresenter.description",
        new_callable=mock.PropertyMock,
    ) as mock_description:
        annotation = factories.Annotation()

        feed = atom.feed_from_annotations(
            [annotation], "atom_url", lambda annotation: "annotation url"
        )

        mock_description.assert_called_once_with()
        assert feed["entries"][0]["content"] == mock_description.return_value


@mock.patch("h.feeds.util")
def test_annotation_url_links(_, factories):
    """Entries should contain links to the HTML pages for the annotations."""
    annotation = factories.Annotation()
    annotation_url = mock.Mock()

    feed = atom.feed_from_annotations([annotation], "atom_url", annotation_url)

    annotation_url.assert_called_once_with(annotation)
    assert feed["entries"][0]["links"][0] == {
        "rel": "alternate",
        "type": "text/html",
        "href": annotation_url.return_value,
    }


@mock.patch("h.feeds.util")
def test_annotation_api_url_links(_, factories):
    """Entries should contain links to the JSON pages for the annotations."""
    annotation = factories.Annotation()
    annotation_api_url = mock.Mock()

    feed = atom.feed_from_annotations(
        [annotation], "atom_url", mock.Mock(), annotation_api_url=annotation_api_url
    )

    annotation_api_url.assert_called_once_with(annotation)
    assert feed["entries"][0]["links"][1] == {
        "rel": "alternate",
        "type": "application/json",
        "href": annotation_api_url.return_value,
    }


def test_feed_updated():
    annotations = [
        _annotation(
            updated=datetime(
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
            updated=datetime(
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
            updated=datetime(
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

    feed = atom.feed_from_annotations(
        annotations, "atom_url", lambda annotation: "annotation url"
    )

    assert feed["updated"] == "2015-03-11T10:45:54.537626+00:00"
