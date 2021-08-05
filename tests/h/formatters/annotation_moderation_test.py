from unittest.mock import create_autospec

import pytest

from h.formatters.annotation_moderation import AnnotationModerationFormatter
from h.security.permissions import Permission
from h.services.flag_count import FlagCountService


class TestAnnotationModerationFormatter:
    def test_preload_sets_flag_counts(self, formatter, flagged, unflagged):
        preload = formatter.preload([flagged.id, unflagged.id])

        assert preload == {flagged.id: 2, unflagged.id: 0}

    def test_preload_skipped_without_user(self, flag_count_svc):
        formatter = AnnotationModerationFormatter(
            flag_count_svc, user=None, has_permission=None
        )
        assert formatter.preload(["annotation-id"]) is None

    def test_preload_skipped_without_ids(self, formatter):
        assert formatter.preload([]) is None

    def test_format_returns_empty_for_non_moderator(
        self, formatter, has_permission, flagged, AnnotationContext
    ):
        has_permission.return_value = False

        assert formatter.format(flagged) == {}

        AnnotationContext.assert_called_once_with(flagged)
        has_permission.assert_called_once_with(
            Permission.Annotation.MODERATE, AnnotationContext.return_value
        )

    def test_format_returns_flag_count_for_moderator(self, formatter, flagged):
        output = formatter.format(flagged)

        assert output == {"moderation": {"flagCount": 2}}

    def test_format_returns_zero_flag_count(self, formatter, unflagged):
        output = formatter.format(unflagged)

        assert output == {"moderation": {"flagCount": 0}}

    def test_format_for_preloaded_annotation(self, formatter, flagged):
        formatter.preload([flagged.id])
        output = formatter.format(flagged)
        assert output == {"moderation": {"flagCount": 2}}

    @pytest.fixture
    def user(self, factories):
        return factories.User()

    @pytest.fixture
    def has_permission(self, pyramid_request):
        return create_autospec(pyramid_request.has_permission)

    @pytest.fixture
    def flagged(self, factories):
        annotation = factories.Annotation()
        factories.Flag.create_batch(2, annotation=annotation)
        return annotation

    @pytest.fixture
    def unflagged(self, factories):
        return factories.Annotation()

    @pytest.fixture
    def formatter(self, flag_count_svc, user, has_permission):
        """Return a formatter with the most common configuration."""
        return AnnotationModerationFormatter(flag_count_svc, user, has_permission)

    @pytest.fixture
    def flag_count_svc(self, db_session):
        # TODO! - This should really be mocked - We are likely re-testing code
        return FlagCountService(db_session)

    @pytest.fixture
    def AnnotationContext(self, patch):
        return patch("h.formatters.annotation_moderation.AnnotationContext")
