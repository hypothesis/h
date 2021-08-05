import datetime

import pytest

from h.presenters.annotation_base import AnnotationBasePresenter, utc_iso8601


class TestAnnotationBasePresenter:
    def test_constructor_args(self, annotation):
        presenter = AnnotationBasePresenter(annotation)

        assert presenter.annotation == annotation

    @pytest.mark.parametrize(
        "created,expected",
        (
            (None, None),
            (
                datetime.datetime(2012, 3, 14, 23, 34, 47, 12),
                "2012-03-14T23:34:47.000012+00:00",
            ),
        ),
    )
    def test_created(self, annotation, created, expected):
        annotation.created = created

        created = AnnotationBasePresenter(annotation).created

        assert created == expected

    @pytest.mark.parametrize(
        "updated,expected",
        (
            (None, None),
            (
                datetime.datetime(1983, 8, 31, 7, 18, 20, 98763),
                "1983-08-31T07:18:20.098763+00:00",
            ),
        ),
    )
    def test_updated_returns_none_if_missing(self, annotation, updated, expected):
        annotation.updated = updated

        updated = AnnotationBasePresenter(annotation).updated

        assert updated == expected

    @pytest.mark.parametrize("text,expected", ((None, ""), ("text", "text")))
    def test_text(self, annotation, text, expected):
        annotation.text = text

        presenter = AnnotationBasePresenter(annotation)

        assert presenter.text == expected

    @pytest.mark.parametrize(
        "tags,expected",
        ((None, []), (["interesting", "magic"], ["interesting", "magic"])),
    )
    def test_tags(self, annotation, tags, expected):
        annotation.tags = tags
        presenter = AnnotationBasePresenter(annotation)

        assert presenter.tags == expected

    def test_target(self, annotation):
        target = AnnotationBasePresenter(annotation).target

        assert target == [
            {"source": annotation.target_uri, "selector": annotation.target_selectors}
        ]

    def test_target_missing_selectors(self, annotation):
        annotation.target_selectors = None

        target = AnnotationBasePresenter(annotation).target

        assert target == [{"source": annotation.target_uri}]

    @pytest.fixture
    def annotation(self, factories):
        return factories.Annotation.build()


class Berlin(datetime.tzinfo):
    """Berlin timezone, without DST support."""

    def dst(self, dt):
        return datetime.timedelta()


def test_utc_iso8601():
    t = datetime.datetime(2016, 2, 24, 18, 3, 25, 7685)
    assert utc_iso8601(t) == "2016-02-24T18:03:25.007685+00:00"


def test_utc_iso8601_ignores_timezone():
    t = datetime.datetime(2016, 2, 24, 18, 3, 25, 7685, Berlin())
    assert utc_iso8601(t) == "2016-02-24T18:03:25.007685+00:00"
