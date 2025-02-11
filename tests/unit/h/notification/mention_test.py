from unittest.mock import call

import pytest

from h.notification.mention import MentionNotification, get_notifications


class TestGetNotifications:
    def test_it(
        self, annotation, mentioning_user, mentioned_user, pyramid_request, user_service
    ):
        result = get_notifications(pyramid_request, annotation, "create")

        user_service.fetch.assert_has_calls(
            [call(mentioning_user.userid), call(mentioned_user.userid)]
        )

        assert len(result) == 1
        assert isinstance(result[0], MentionNotification)
        assert result[0].mentioning_user == mentioning_user
        assert result[0].mentioned_user == mentioned_user
        assert result[0].annotation == annotation
        assert result[0].document == annotation.document

    def test_it_returns_empty_list_when_action_is_not_create(
        self, pyramid_request, annotation
    ):
        assert get_notifications(pyramid_request, annotation, "NOT_CREATE") == []

    def test_it_returns_empty_list_when_mentioning_user_does_not_exist(
        self, pyramid_request, annotation, user_service, factories
    ):
        user_service.fetch.side_effect = (None, factories.User())

        assert get_notifications(pyramid_request, annotation, "create") == []

    def test_it_returns_empty_list_when_mentioned_user_does_not_exist(
        self, pyramid_request, annotation, user_service, factories
    ):
        user_service.fetch.side_effect = (factories.User(), None)

        assert get_notifications(pyramid_request, annotation, "create") == []

    def test_it_returns_empty_list_when_mentioned_user_has_no_email_address(
        self, pyramid_request, annotation, mentioned_user
    ):
        mentioned_user.email = None
        assert get_notifications(pyramid_request, annotation, "create") == []

    def test_it_returns_empty_list_when_annotation_document_is_empty(
        self, pyramid_request, annotation
    ):
        annotation.document = None

        assert get_notifications(pyramid_request, annotation, "create") == []

    def test_it_returns_empty_list_when_self_mention(
        self, pyramid_request, annotation, user_service, mentioning_user
    ):
        user_service.fetch.side_effect = (mentioning_user, mentioning_user)

        assert get_notifications(pyramid_request, annotation, "create") == []

    @pytest.fixture
    def annotation(self, factories, mentioning_user, mention):
        return factories.Annotation(
            userid=mentioning_user.userid, shared=True, mentions=[mention]
        )

    @pytest.fixture
    def mentioned_user(self, factories):
        return factories.User(nipsa=False)

    @pytest.fixture
    def mentioning_user(self, factories):
        return factories.User(nipsa=False)

    @pytest.fixture
    def mention(self, factories, mentioned_user):
        return factories.Mention(user=mentioned_user)

    @pytest.fixture(autouse=True)
    def user_service(self, user_service, mentioning_user, mentioned_user):
        user_service.fetch.side_effect = (mentioning_user, mentioned_user)
        return user_service
