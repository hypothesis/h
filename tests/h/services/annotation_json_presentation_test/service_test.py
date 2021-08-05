from unittest.mock import sentinel

import pytest
from sqlalchemy import event

from h.services.annotation_json_presentation import AnnotationJSONPresentationService


class TestAnnotationJSONPresentationService:
    def test_it_configures_formatters(
        self, svc, formatters, db_session, flag_service, moderation_service
    ):
        formatters.AnnotationFlagFormatter.assert_called_once_with(
            sentinel.flag_svc, sentinel.user
        )
        formatters.AnnotationHiddenFormatter.assert_called_once_with(
            sentinel.has_permission, sentinel.user
        )
        formatters.AnnotationModerationFormatter.assert_called_once_with(
            sentinel.flag_count_svc, sentinel.user, sentinel.has_permission
        )
        formatters.AnnotationUserInfoFormatter.assert_called_once_with(
            db_session, sentinel.user_svc
        )

        assert svc.formatters == [
            formatters.AnnotationFlagFormatter.return_value,
            formatters.AnnotationHiddenFormatter.return_value,
            formatters.AnnotationModerationFormatter.return_value,
            formatters.AnnotationUserInfoFormatter.return_value,
        ]

    def test_present(self, svc, annotation, AnnotationJSONPresenter):
        result = svc.present(annotation)

        AnnotationJSONPresenter.assert_called_once_with(
            annotation, links_service=svc.links_svc, formatters=svc.formatters
        )

        assert result == AnnotationJSONPresenter.return_value.asdict.return_value

    def test_present_all(self, svc, factories, annotation, AnnotationJSONPresenter):
        annotation_ids = [annotation.id]

        result = svc.present_all(annotation_ids)

        for formatter in svc.formatters:
            formatter.preload.assert_called_once_with(annotation_ids)

        AnnotationJSONPresenter.assert_called_once_with(
            annotation, links_service=svc.links_svc, formatters=svc.formatters
        )
        assert result == [
            AnnotationJSONPresenter.return_value.asdict.return_value,
        ]

    @pytest.mark.parametrize("property", ("document", "moderation"))
    @pytest.mark.parametrize("with_preload", (True, False))
    def test_present_all_preloading_is_effective(
        self, svc, annotation, db_session, query_counter, property, with_preload
    ):
        # Ensure SQLAlchemy forgets all about our annotation
        db_session.flush()
        db_session.expire(annotation)
        if with_preload:
            svc.present_all([annotation.id])

        query_counter.reset()
        getattr(annotation, property)

        # If we preloaded, we shouldn't execute any queries (and vice versa)
        assert bool(query_counter.count) != with_preload

    @pytest.fixture
    def query_counter(self, db_engine):
        class QueryCounter:
            count = 0

            def __call__(self, *args, **kwargs):
                print(args, kwargs)
                self.count += 1

            def reset(self):
                self.count = 0

        query_counter = QueryCounter()
        event.listen(db_engine, "before_cursor_execute", query_counter)
        return query_counter

    @pytest.fixture
    def svc(self, db_session):
        return AnnotationJSONPresentationService(
            session=db_session,
            user=sentinel.user,
            links_svc=sentinel.links_svc,
            flag_svc=sentinel.flag_svc,
            flag_count_svc=sentinel.flag_count_svc,
            user_svc=sentinel.user_svc,
            has_permission=sentinel.has_permission,
        )

    @pytest.fixture
    def annotation(self, factories):
        return factories.Annotation()

    @pytest.fixture(autouse=True)
    def formatters(self, patch):
        return patch("h.services.annotation_json_presentation.service.formatters")

    @pytest.fixture(autouse=True)
    def AnnotationJSONPresenter(self, patch):
        return patch(
            "h.services.annotation_json_presentation.service.AnnotationJSONPresenter"
        )
