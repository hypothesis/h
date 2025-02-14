from unittest.mock import sentinel

import pytest

from h.services.mention import MentionService, factory


class TestMentionService:
    def test_update_mentions(self, service, annotation, mentioned_user):
        service.update_mentions(annotation)

        assert len(annotation.mentions) == 1
        assert annotation.mentions[0].user == mentioned_user

    def test_update_mentions_with_nipsa_mentioned_user(
        self, service, annotation, mentioned_user
    ):
        mentioned_user.nipsa = True

        service.update_mentions(annotation)

        assert len(annotation.mentions) == 0

    def test_update_mentions_with_nipsa_mentioning_user(
        self, service, annotation, annotation_slim
    ):
        annotation_slim.user.nipsa = True

        service.update_mentions(annotation)

        assert len(annotation.mentions) == 0

    def test_update_mentions_with_more_than_mention_limit(
        self,
        service,
        user_service,
        annotation,
        mentioned_user,
        factories,
        patch,
    ):
        mentioned_user2 = factories.User()
        annotation.text = (
            f'Hello <a data-hyp-mention data-userid="{mentioned_user.userid}">@{mentioned_user.display_name}</a>'
            f'Hello <a data-hyp-mention data-userid="{mentioned_user2.userid}">@{mentioned_user2.display_name}</a>'
        )
        user_service.fetch_all.return_value = [mentioned_user, mentioned_user2]
        limit = patch("h.services.mention.MENTION_LIMIT", new=1, autospec=False)

        service.update_mentions(annotation)

        assert len(annotation.mentions) == limit

    def test_update_mentions_with_groupid_not_world(
        self, service, annotation, factories
    ):
        group = factories.Group()
        annotation.groupid = group.pubid

        service.update_mentions(annotation)

        assert len(annotation.mentions) == 0

    @pytest.fixture
    def annotation(self, annotation_slim, mentioned_user):
        annotation = annotation_slim.annotation
        annotation.text = f'Hello <a data-hyp-mention data-userid="{mentioned_user.userid}">@{mentioned_user.display_name}</a>'
        annotation.shared = True
        return annotation

    @pytest.fixture
    def annotation_slim(self, factories, mentioning_user):
        return factories.AnnotationSlim(user=mentioning_user)

    @pytest.fixture
    def mentioning_user(self, factories):
        return factories.User(nipsa=False)

    @pytest.fixture
    def mentioned_user(self, factories):
        return factories.User(nipsa=False)

    @pytest.fixture
    def user_service(self, user_service, annotation_slim, mentioned_user):
        user_service.fetch.return_value = annotation_slim.user
        user_service.fetch_all.return_value = [mentioned_user]
        return user_service

    @pytest.fixture
    def service(self, db_session, user_service):
        return MentionService(db_session, user_service)


class TestFactory:
    def test_it(self, pyramid_request, user_service, MentionService):
        service = factory(sentinel.context, pyramid_request)

        MentionService.assert_called_once_with(
            session=pyramid_request.db,
            user_service=user_service,
        )

        assert service == MentionService.return_value

    @pytest.fixture
    def MentionService(self, patch):
        return patch("h.services.mention.MentionService")
