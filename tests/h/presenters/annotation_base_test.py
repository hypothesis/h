import datetime
from unittest import mock

from pytz import timezone

from h.presenters.annotation_base import AnnotationBasePresenter, utc_iso8601


class TestAnnotationBasePresenter:
    def test_constructor_args(self):
        annotation = mock.Mock()
        context = mock.Mock(annotation=annotation)

        presenter = AnnotationBasePresenter(context)

        assert presenter.annotation_context == context
        assert presenter.annotation == annotation

    def test_created_returns_none_if_missing(self):
        annotation = mock.Mock(created=None)
        context = mock.Mock(annotation=annotation)

        created = AnnotationBasePresenter(context).created

        assert created is None

    def test_created_uses_iso_format(self):
        when = datetime.datetime(2012, 3, 14, 23, 34, 47, 12)
        annotation = mock.Mock(created=when)
        context = mock.Mock(annotation=annotation)

        created = AnnotationBasePresenter(context).created

        assert created == "2012-03-14T23:34:47.000012+00:00"

    def test_updated_returns_none_if_missing(self):
        annotation = mock.Mock(updated=None)
        context = mock.Mock(annotation=annotation)

        updated = AnnotationBasePresenter(context).updated

        assert updated is None

    def test_updated_uses_iso_format(self):
        when = datetime.datetime(1983, 8, 31, 7, 18, 20, 98763)
        annotation = mock.Mock(updated=when)
        context = mock.Mock(annotation=annotation)

        updated = AnnotationBasePresenter(context).updated

        assert updated == "1983-08-31T07:18:20.098763+00:00"

    def test_links(self):
        annotation = mock.Mock()
        context = mock.Mock(annotation=annotation)

        links = AnnotationBasePresenter(context).links
        assert links == context.links

    def test_text(self):
        annotation = mock.Mock(text="It is magical!")
        context = mock.Mock(annotation=annotation)
        presenter = AnnotationBasePresenter(context)

        assert presenter.text == "It is magical!"

    def test_text_missing(self):
        annotation = mock.Mock(text=None)
        context = mock.Mock(annotation=annotation)
        presenter = AnnotationBasePresenter(context)

        assert not presenter.text

    def test_tags(self):
        annotation = mock.Mock(tags=["interesting", "magic"])
        context = mock.Mock(annotation=annotation)
        presenter = AnnotationBasePresenter(context)

        assert ["interesting", "magic"] == presenter.tags

    def test_tags_missing(self):
        annotation = mock.Mock(tags=None)
        context = mock.Mock(annotation=annotation)
        presenter = AnnotationBasePresenter(context)

        assert [] == presenter.tags

    def test_target(self):
        annotation = mock.Mock(
            target_uri="http://example.com",
            target_selectors={"PositionSelector": {"start": 0, "end": 12}},
        )
        context = mock.Mock(annotation=annotation)

        expected = [
            {
                "source": "http://example.com",
                "selector": {"PositionSelector": {"start": 0, "end": 12}},
            }
        ]
        actual = AnnotationBasePresenter(context).target
        assert expected == actual

    def test_target_missing_selectors(self):
        annotation = mock.Mock(target_uri="http://example.com", target_selectors=None)
        context = mock.Mock(annotation=annotation)

        expected = [{"source": "http://example.com"}]
        actual = AnnotationBasePresenter(context).target
        assert expected == actual


class Berlin(datetime.tzinfo):
    """Berlin timezone, without DST support"""

    def dst(self, dt):
        return datetime.timedelta()


def test_utc_iso8601():
    t = datetime.datetime(2016, 2, 24, 18, 3, 25, 7685)
    assert utc_iso8601(t) == "2016-02-24T18:03:25.007685+00:00"


def test_utc_iso8601_ignores_timezone():
    t = datetime.datetime(2016, 2, 24, 18, 3, 25, 7685, Berlin())
    assert utc_iso8601(t) == "2016-02-24T18:03:25.007685+00:00"
