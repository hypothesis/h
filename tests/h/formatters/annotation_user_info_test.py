import pytest

from h.formatters.annotation_user_info import AnnotationUserInfoFormatter


class TestAnnotationUserInfoFormatter:
    def test_it(self, user_info, factories):
        annotation = factories.Annotation()

        result = AnnotationUserInfoFormatter().format(annotation)

        user_info.assert_called_once_with(annotation.user)
        assert result == user_info.return_value

    @pytest.fixture
    def user_info(self, patch):
        return patch("h.formatters.annotation_user_info.user_info")
