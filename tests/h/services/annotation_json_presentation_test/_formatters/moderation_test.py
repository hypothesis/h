from unittest.mock import create_autospec, sentinel

import pytest

from h.security.permissions import Permission
from h.services.annotation_json_presentation._formatters import ModerationFormatter


class TestModerationFormatter:
    def test_preload_sets_flag_counts(self, formatter, flag_service):
        flag_service.flag_counts.return_value = {"flagged": 2, "unflagged": 0}

        preload = formatter.preload(sentinel.ids)

        flag_service.flag_counts.assert_called_once_with(sentinel.ids)

        assert preload == flag_service.flag_counts.return_value
        assert formatter._cache == flag_service.flag_counts.return_value

    def test_preload_skipped_without_user(self, flag_service):
        formatter = ModerationFormatter(
            flag_service, user=None, has_permission=sentinel.has_permission
        )

        formatter.preload(sentinel.ids)

        flag_service.flag_counts.assert_not_called()

    def test_preload_skipped_without_ids(self, formatter, flag_service):
        formatter.preload([])

        flag_service.flag_counts.assert_not_called()

    def test_format_returns_empty_for_non_moderator(
        self, formatter, has_permission, annotation, AnnotationContext
    ):
        has_permission.return_value = False

        assert formatter.format(annotation) == {}

        AnnotationContext.assert_called_once_with(annotation)
        has_permission.assert_called_once_with(
            Permission.Annotation.MODERATE, AnnotationContext.return_value
        )

    def test_format_returns_flag_count_for_moderator(
        self, formatter, annotation, flag_service, has_permission
    ):
        has_permission.return_value = True

        output = formatter.format(annotation)

        flag_service.flag_count.assert_called_once_with(annotation)
        assert output == {
            "moderation": {"flagCount": flag_service.flag_count.return_value}
        }

    def test_format_uses_the_cache_from_preloading(
        self, formatter, annotation, flag_service
    ):
        flag_service.flag_counts.return_value = {annotation.id: 1}
        formatter.preload([annotation.id])

        output = formatter.format(annotation)

        assert output == {"moderation": {"flagCount": 1}}
        flag_service.flag_count.assert_not_called()

    @pytest.fixture
    def has_permission(self, pyramid_request):
        return create_autospec(pyramid_request.has_permission)

    @pytest.fixture
    def annotation(self, factories):
        return factories.Annotation()

    @pytest.fixture
    def formatter(self, flag_service, factories, has_permission):
        return ModerationFormatter(flag_service, factories.User(), has_permission)

    @pytest.fixture
    def AnnotationContext(self, patch):
        return patch(
            "h.services.annotation_json_presentation._formatters.moderation.AnnotationContext"
        )
