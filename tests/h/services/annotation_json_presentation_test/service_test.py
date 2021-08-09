from unittest.mock import sentinel

import pytest
from sqlalchemy import event

from h.services.annotation_json_presentation import AnnotationJSONPresentationService


class TestAnnotationJSONPresentationService:
    def test_it_configures_formatters(self, svc, _formatters, db_session, flag_service):
        _formatters.HiddenFormatter.assert_called_once_with(
            sentinel.has_permission, sentinel.user
        )
        _formatters.ModerationFormatter.assert_called_once_with(
            flag_service, sentinel.user, sentinel.has_permission
        )

        assert svc.formatters == [
            _formatters.HiddenFormatter.return_value,
            _formatters.ModerationFormatter.return_value,
        ]

    def test_present(self, svc, annotation, AnnotationJSONPresenter, flag_service):
        AnnotationJSONPresenter.return_value.asdict.return_value = {"presenter": 1}
        for formatter in svc.formatters:
            formatter.format.return_value = {formatter.__class__.__name__: 1}

        result = svc.present(annotation)

        AnnotationJSONPresenter.assert_called_once_with(
            annotation, links_service=svc.links_svc
        )
        for formatter in svc.formatters:
            formatter.format.assert_called_once_with(annotation)

        flag_service.flagged.assert_called_once_with(sentinel.user, annotation)
        assert result == {
            "presenter": 1,
            "HiddenFormatter": 1,
            "ModerationFormatter": 1,
            "flagged": flag_service.flagged.return_value,
        }

    def test_present_all(
        self, svc, factories, annotation, AnnotationJSONPresenter, flag_service
    ):
        annotation_ids = [annotation.id]

        result = svc.present_all(annotation_ids)

        for formatter in svc.formatters:
            formatter.preload.assert_called_once_with(annotation_ids)

        flag_service.all_flagged.assert_called_once_with(sentinel.user, annotation_ids)
        AnnotationJSONPresenter.assert_called_once_with(
            annotation, links_service=svc.links_svc
        )
        assert result == [
            AnnotationJSONPresenter.return_value.asdict.return_value,
        ]

    @pytest.mark.parametrize("property", ("document", "moderation", "user"))
    @pytest.mark.parametrize("with_preload", (True, False))
    def test_present_all_preloading_is_effective(
        self, svc, factories, db_session, query_counter, property, with_preload
    ):
        # Ensure SQLAlchemy forgets all about our annotation
        annotations = factories.Annotation.create_batch(size=3)
        annotation_ids = [annotation.id for annotation in annotations]
        db_session.flush()
        db_session.expire_all()
        query_counter.reset()

        if with_preload:
            svc.present_all(annotation_ids)

            # Check we aren't just issuing millions of queries to make this
            # happen. There should be one for each type (annotation, doc, etc)
            assert query_counter.count == 4

        query_counter.reset()
        getattr(annotations[0], property)
        getattr(annotations[1], property)

        # If we preloaded, we shouldn't execute any queries (and vice versa)
        assert bool(query_counter.count) != with_preload

    @pytest.fixture
    def query_counter(self, db_engine):
        class QueryCounter:
            count = 0

            def __call__(self, *args, **kwargs):
                self.count += 1

            def reset(self):
                self.count = 0

        query_counter = QueryCounter()
        event.listen(db_engine, "before_cursor_execute", query_counter)
        return query_counter

    @pytest.fixture
    def svc(self, db_session, flag_service):
        return AnnotationJSONPresentationService(
            session=db_session,
            user=sentinel.user,
            links_svc=sentinel.links_svc,
            flag_svc=flag_service,
            has_permission=sentinel.has_permission,
        )

    @pytest.fixture
    def annotation(self, factories):
        return factories.Annotation()

    @pytest.fixture(autouse=True)
    def _formatters(self, patch):
        return patch("h.services.annotation_json_presentation.service._formatters")

    @pytest.fixture(autouse=True)
    def AnnotationJSONPresenter(self, patch):
        return patch(
            "h.services.annotation_json_presentation.service.AnnotationJSONPresenter"
        )
