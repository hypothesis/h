from unittest.mock import sentinel

import pytest
from h_matchers import Any
from sqlalchemy import event

from h.security.permissions import Permission
from h.services.annotation_json_presentation import AnnotationJSONPresentationService
from h.traversal import AnnotationContext


class TestAnnotationJSONPresentationService:
    def test_present(self, service, BasicJSONPresenter):
        result = service.present(annotation=sentinel.annotation)

        BasicJSONPresenter.return_value.present.assert_called_once_with(
            sentinel.annotation
        )
        assert result == BasicJSONPresenter.return_value.present.return_value

    def test_present_for_user(
        self, service, user, annotation, BasicJSONPresenter, flag_service
    ):
        BasicJSONPresenter.return_value.present.return_value = {"presenter": 1}

        result = service.present_for_user(annotation, user)

        BasicJSONPresenter.return_value.present.assert_called_once_with(annotation)
        flag_service.flagged.assert_called_once_with(user, annotation)
        flag_service.flag_count.assert_called_once_with(annotation)
        assert result == {
            "presenter": 1,
            "hidden": False,
            "flagged": flag_service.flagged.return_value,
            "moderation": {"flagCount": flag_service.flag_count.return_value},
        }

    def test_present_for_user_only_shows_moderation_to_moderators(
        self, service, annotation, user, identity_permits, Identity
    ):
        identity_permits.return_value = False

        result = service.present_for_user(annotation, user)

        Identity.from_models.assert_called_once_with(user=user)
        identity_permits.assert_called_once_with(
            identity=Identity.from_models.return_value,
            context=Any.instance_of(AnnotationContext).with_attrs(
                {"annotation": annotation}
            ),
            permission=Permission.Annotation.MODERATE,
        )

        assert "moderation" not in result

    @pytest.mark.usefixtures("with_hidden_annotation")
    def test_present_for_user_hidden_status_is_not_shown_to_creator(
        self, service, annotation, user
    ):
        annotation.userid = user.userid

        result = service.present_for_user(annotation, user)

        assert not result["hidden"]

    @pytest.mark.usefixtures("with_hidden_annotation")
    def test_present_for_user_hidden_censors_content_for_normal_users(
        self, service, annotation, user, identity_permits
    ):
        identity_permits.return_value = False

        result = service.present_for_user(annotation, user)

        assert result["hidden"]
        assert not result["text"]
        assert not result["tags"]

    @pytest.mark.usefixtures("with_hidden_annotation")
    def test_present_for_user_hidden_shows_everything_to_moderators(
        self, service, annotation, user, identity_permits, BasicJSONPresenter
    ):
        identity_permits.return_value = True
        BasicJSONPresenter.return_value.present.return_value = {
            "text": sentinel.text,
            "tags": [sentinel.tags],
        }

        result = service.present_for_user(annotation, user)

        assert result["hidden"]
        assert result["text"]
        assert result["tags"]

    def test_present_all_for_user(
        self,
        service,
        annotation,
        user,
        BasicJSONPresenter,
        flag_service,
        user_service,
    ):
        annotation_ids = [annotation.id]

        result = service.present_all_for_user(annotation_ids, user)

        flag_service.all_flagged.assert_called_once_with(user, annotation_ids)
        flag_service.flag_counts.assert_called_once_with(annotation_ids)
        user_service.fetch_all.assert_called_once_with([annotation.userid])
        BasicJSONPresenter.return_value.present.assert_called_once_with(annotation)
        assert result == [
            BasicJSONPresenter.return_value.present.return_value,
        ]

    @pytest.mark.parametrize("attribute", ("document", "moderation", "group"))
    @pytest.mark.parametrize("with_preload", (True, False))
    def test_present_all_for_userpreloading_is_effective(
        self,
        service,
        annotation,
        user,
        db_session,
        query_counter,
        attribute,
        with_preload,
    ):
        # Ensure SQLAlchemy forgets all about our annotation
        db_session.flush()
        db_session.expire(annotation)
        if with_preload:
            service.present_all_for_user([annotation.id], user)

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
    def service(self, db_session, flag_service, user_service):
        return AnnotationJSONPresentationService(
            session=db_session,
            links_service=sentinel.links_service,
            flag_service=flag_service,
            user_service=user_service,
        )

    @pytest.fixture
    def user(self, factories):
        return factories.User()

    @pytest.fixture
    def annotation(self, factories):
        return factories.Annotation(moderation=None)

    @pytest.fixture
    def with_hidden_annotation(self, annotation, factories):
        annotation.moderation = factories.AnnotationModeration()

    @pytest.fixture(autouse=True)
    def Identity(self, patch):
        return patch("h.services.annotation_json_presentation.service.Identity")

    @pytest.fixture(autouse=True)
    def identity_permits(self, patch):
        return patch("h.services.annotation_json_presentation.service.identity_permits")

    @pytest.fixture(autouse=True)
    def BasicJSONPresenter(self, patch):
        BasicJSONPresenter = patch(
            "h.services.annotation_json_presentation.service.BasicJSONPresenter"
        )
        BasicJSONPresenter.return_value.present.return_value = {}
        return BasicJSONPresenter
