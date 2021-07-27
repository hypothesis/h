from collections import namedtuple
from unittest.mock import create_autospec

import pytest

from h.formatters.annotation_moderation import AnnotationModerationFormatter
from h.security.permissions import Permission
from h.services.flag_count import FlagCountService

FakeAnnotationContext = namedtuple("FakeAnnotationContext", ["annotation", "group"])


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
        self, formatter, has_permission, flagged, group
    ):
        has_permission.return_value = False

        annotation_context = FakeAnnotationContext(flagged, group)

        assert formatter.format(annotation_context) == {}
        has_permission.assert_called_once_with(
            Permission.Annotation.MODERATE, annotation_context
        )

    def test_format_returns_flag_count_for_moderator(self, formatter, group, flagged):
        annotation_context = FakeAnnotationContext(flagged, group)

        output = formatter.format(annotation_context)
        assert output == {"moderation": {"flagCount": 2}}

    def test_format_returns_zero_flag_count(self, formatter, group, unflagged):
        annotation_context = FakeAnnotationContext(unflagged, group)

        output = formatter.format(annotation_context)
        assert output == {"moderation": {"flagCount": 0}}

    def test_format_for_preloaded_annotation(self, formatter, group, flagged):
        annotation_context = FakeAnnotationContext(flagged, group)

        formatter.preload([flagged.id])
        output = formatter.format(annotation_context)
        assert output == {"moderation": {"flagCount": 2}}

    @pytest.fixture
    def user(self, factories):
        return factories.User()

    @pytest.fixture
    def group(self, factories):
        return factories.Group()

    @pytest.fixture
    def has_permission(self):
        def has_permission(permission, context):
            """Return if we can do something in a context."""

        return create_autospec(has_permission)

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
        """A formatter with the most common configuration."""
        return AnnotationModerationFormatter(flag_count_svc, user, has_permission)

    @pytest.fixture
    def flag_count_svc(self, db_session):
        return FlagCountService(db_session)
