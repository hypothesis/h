from unittest.mock import create_autospec, sentinel

import pytest
from h_matchers import Any
from sqlalchemy import event

from h.security.permissions import Permission
from h.services.annotation_json_presentation import AnnotationJSONPresentationService
from h.traversal import AnnotationContext


class TestAnnotationJSONPresentationService:
    def test_present(
        self, svc, user, annotation, AnnotationJSONPresenter, flag_service, user_service
    ):
        AnnotationJSONPresenter.return_value.asdict.return_value = {"presenter": 1}

        result = svc.present(annotation)

        AnnotationJSONPresenter.assert_called_once_with(
            annotation, links_service=svc.links_svc, user_service=user_service
        )

        flag_service.flagged.assert_called_once_with(user, annotation)
        flag_service.flag_count.assert_called_once_with(annotation)
        assert result == {
            "presenter": 1,
            "hidden": False,
            "flagged": flag_service.flagged.return_value,
            "moderation": {"flagCount": flag_service.flag_count.return_value},
        }

    def test_present_only_shows_moderation_to_moderators(
        self, svc, annotation, has_permission
    ):
        has_permission.return_value = False

        result = svc.present(annotation)

        has_permission.assert_called_once_with(
            Permission.Annotation.MODERATE,
            context=Any.instance_of(AnnotationContext).with_attrs(
                {"annotation": annotation}
            ),
        )

        assert "moderation" not in result

    @pytest.mark.usefixtures("with_hidden_annotation")
    def test_present_hidden_status_is_not_shown_to_creator(self, svc, user, annotation):
        annotation.userid = user.userid

        result = svc.present(annotation)

        assert not result["hidden"]

    @pytest.mark.usefixtures("with_hidden_annotation")
    def test_present_hidden_censors_content_for_normal_users(
        self, svc, annotation, has_permission
    ):
        has_permission.return_value = False

        result = svc.present(annotation)

        assert result["hidden"]
        assert not result["text"]
        assert not result["tags"]

    @pytest.mark.usefixtures("with_hidden_annotation")
    def test_present_hidden_shows_everything_to_moderators(
        self, svc, annotation, has_permission, AnnotationJSONPresenter
    ):
        has_permission.return_value = True
        AnnotationJSONPresenter.return_value.asdict.return_value = {
            "text": sentinel.text,
            "tags": [sentinel.tags],
        }

        result = svc.present(annotation)

        assert result["hidden"]
        assert result["text"]
        assert result["tags"]

    def test_present_all(
        self,
        svc,
        user,
        factories,
        annotation,
        AnnotationJSONPresenter,
        flag_service,
        user_service,
    ):
        annotation_ids = [annotation.id]

        result = svc.present_all(annotation_ids)

        flag_service.all_flagged.assert_called_once_with(user, annotation_ids)
        flag_service.flag_counts.assert_called_once_with(annotation_ids)
        user_service.fetch_all.assert_called_once_with([annotation.userid])
        AnnotationJSONPresenter.assert_called_once_with(
            annotation, links_service=svc.links_svc, user_service=user_service
        )
        assert result == [
            AnnotationJSONPresenter.return_value.asdict.return_value,
        ]

    @pytest.mark.parametrize("attribute", ("document", "moderation", "group"))
    @pytest.mark.parametrize("with_preload", (True, False))
    def test_present_all_preloading_is_effective(
        self, svc, annotation, db_session, query_counter, attribute, with_preload
    ):
        # Ensure SQLAlchemy forgets all about our annotation
        db_session.flush()
        db_session.expire(annotation)
        if with_preload:
            svc.present_all([annotation.id])

        query_counter.reset()
        getattr(annotation, attribute)

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
    def svc(self, db_session, user, flag_service, user_service, has_permission):
        return AnnotationJSONPresentationService(
            session=db_session,
            user=user,
            links_svc=sentinel.links_svc,
            flag_svc=flag_service,
            user_svc=user_service,
            has_permission=has_permission,
        )

    @pytest.fixture
    def user(self, factories):
        return factories.User()

    @pytest.fixture
    def annotation(self, factories):
        return factories.Annotation(moderation=None)

    @pytest.fixture
    def has_permission(self, pyramid_request):
        return create_autospec(pyramid_request.has_permission)

    @pytest.fixture
    def with_hidden_annotation(self, annotation, factories):
        annotation.moderation = factories.AnnotationModeration()

    @pytest.fixture(autouse=True)
    def AnnotationJSONPresenter(self, patch):
        AnnotationJSONPresenter = patch(
            "h.services.annotation_json_presentation.service.AnnotationJSONPresenter"
        )
        AnnotationJSONPresenter.return_value.asdict.return_value = {}
        return AnnotationJSONPresenter
