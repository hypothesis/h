from unittest.mock import call

import pytest

from h.models import Subscriptions
from h.notification.reply import Notification, get_notification


class TestGetNotification:
    def test_it(
        self,
        annotation,
        parent,
        annotation_user,
        parent_user,
        pyramid_request,
        user_service,
        subscription_service,
        annotation_read_service,
    ):
        result = get_notification(pyramid_request, annotation, "create")

        annotation_read_service.get_annotation_by_id.assert_called_once_with(
            annotation.parent_id
        )
        user_service.fetch.assert_has_calls(
            [call(parent.userid), call(annotation.userid)]
        )
        subscription_service.get_subscription.assert_called_once_with(
            user_id=parent.userid, type_=Subscriptions.Type.REPLY
        )

        assert isinstance(result, Notification)
        assert result.reply == annotation
        assert result.parent == parent
        assert result.reply_user == annotation_user
        assert result.parent_user == parent_user
        assert result.document == annotation.document

    def test_it_returns_none_when_action_is_not_create(
        self, pyramid_request, annotation
    ):
        assert get_notification(pyramid_request, annotation, "NOT_CREATE") is None

    def test_it_returns_none_when_annotation_is_not_reply(
        self, pyramid_request, annotation
    ):
        annotation.references = None

        assert get_notification(pyramid_request, annotation, "create") is None

    def test_it_returns_none_when_parent_does_not_exist(
        self,
        pyramid_request,
        annotation,
        annotation_read_service,
    ):
        annotation_read_service.get_annotation_by_id.return_value = None

        assert get_notification(pyramid_request, annotation, "create") is None

    def test_it_returns_none_when_parent_user_does_not_exist(
        self, pyramid_request, annotation, user_service, factories
    ):
        user_service.fetch.side_effect = (None, factories.User())

        assert get_notification(pyramid_request, annotation, "create") is None

    def test_it_returns_none_when_reply_user_does_not_exist(
        self, pyramid_request, annotation, user_service, factories
    ):
        user_service.fetch.side_effect = (factories.User(), None)

        assert get_notification(pyramid_request, annotation, "create") is None

    def test_it_returns_none_when_parent_user_has_no_email_address(
        self, pyramid_request, annotation, parent_user
    ):
        parent_user.email = None
        assert get_notification(pyramid_request, annotation, "create") is None

    def test_it_returns_none_when_reply_by_same_user(
        self, pyramid_request, annotation, user_service, factories
    ):
        single_user = factories.User()
        user_service.fetch.side_effect = (single_user, single_user)

        assert get_notification(pyramid_request, annotation, "create") is None

    def test_it_returns_none_when_parent_user_cannot_read_reply(
        self, pyramid_request, annotation
    ):
        annotation.shared = False

        assert get_notification(pyramid_request, annotation, "create") is None

    def test_it_returns_none_when_subscription_inactive(
        self, pyramid_request, annotation, subscription_service
    ):
        subscription_service.get_subscription.return_value.active = False

        assert get_notification(pyramid_request, annotation, "create") is None

    # This would all be a lot more pleasant if we had some SQLAlchemy
    # relationships between these very important items
    @pytest.fixture
    def annotation_user(self, factories, db_session):
        annotation_user = factories.User()
        db_session.flush()
        return annotation_user

    @pytest.fixture
    def annotation(self, factories, annotation_user, parent):
        return factories.Annotation(
            userid=annotation_user.userid, shared=True, references=[parent.id]
        )

    @pytest.fixture
    def parent_user(self, factories, db_session):
        parent_user = factories.User()
        db_session.flush()
        return parent_user

    @pytest.fixture
    def parent(self, factories, db_session, parent_user, annotation_read_service):
        parent = factories.Annotation(userid=parent_user.userid)
        db_session.flush()

        annotation_read_service.get_annotation_by_id.return_value = parent
        return parent

    @pytest.fixture(autouse=True)
    def user_service(self, user_service, parent_user, annotation_user):
        user_service.fetch.side_effect = (parent_user, annotation_user)
        return user_service

    @pytest.fixture(autouse=True)
    def subscription_service(self, subscription_service, factories):
        subscription_service.get_subscription.return_value = factories.Subscriptions(
            active=True
        )
        return subscription_service
