import pytest

from h.presenters.annotation_base import AnnotationBasePresenter


class TestAnnotationBasePresenter:
    def test_constructor_args(self, annotation):
        presenter = AnnotationBasePresenter(annotation)

        assert presenter.annotation == annotation

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
