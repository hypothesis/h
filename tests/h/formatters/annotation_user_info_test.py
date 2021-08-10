import pytest

from h.formatters.annotation_user_info import AnnotationUserInfoFormatter


class TestAnnotationUserInfoFormatter:
    def test_preload_fetches_users_by_id(self, formatter, factories, user_service):
        annotation_1 = factories.Annotation()
        annotation_2 = factories.Annotation()

        formatter.preload([annotation_1.id, annotation_2.id])

        user_service.fetch_all.assert_called_once_with(
            {annotation_1.userid, annotation_2.userid}
        )

    def test_preload_skips_fetching_for_empty_ids(self, formatter, user_service):
        formatter.preload([])
        assert not user_service.fetch_all.called

    def test_format_fetches_user_by_id(
        self, formatter, annotation, factories, user_service
    ):
        formatter.format(annotation)

        user_service.fetch.assert_called_once_with(annotation.userid)

    def test_format_uses_user_info(
        self, formatter, annotation, user_service, user_info, factories
    ):
        user = factories.User()
        user_service.fetch.return_value = user

        formatter.format(annotation)

        user_info.assert_called_once_with(user)

    def test_format_returns_formatted_user_info(self, formatter, annotation, user_info):
        result = formatter.format(annotation)

        assert result == user_info.return_value

    @pytest.fixture
    def annotation(self, factories):
        return factories.Annotation.build()

    @pytest.fixture
    def formatter(self, db_session, user_service):
        return AnnotationUserInfoFormatter(db_session, user_service)

    @pytest.fixture
    def user_info(self, patch):
        return patch("h.formatters.annotation_user_info.user_info")
