# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from collections import namedtuple

import pytest

from h.formatters.annotation_moderation import AnnotationModerationFormatter
from h.services.flag_count import FlagCountService

FakeAnnotationContext = namedtuple("FakeAnnotationContext", ["annotation", "group"])


class FakePermissionCheck(object):
    def __init__(self):
        self._permissions = {}

    def add_permission(self, permission, context, granted):
        self._permissions[(permission, context)] = granted

    def __call__(self, permission, context):
        return self._permissions[(permission, context)]


class TestAnnotationModerationFormatter(object):
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
        self, flag_count_svc, user, group, flagged, permission_denied
    ):
        formatter = AnnotationModerationFormatter(
            flag_count_svc, user, permission_denied
        )
        annotation_resource = FakeAnnotationContext(flagged, group)

        assert formatter.format(annotation_resource) == {}

    def test_format_returns_flag_count_for_moderator(self, formatter, group, flagged):
        annotation_resource = FakeAnnotationContext(flagged, group)

        output = formatter.format(annotation_resource)
        assert output == {"moderation": {"flagCount": 2}}

    def test_format_returns_zero_flag_count(self, formatter, group, unflagged):
        annotation_resource = FakeAnnotationContext(unflagged, group)

        output = formatter.format(annotation_resource)
        assert output == {"moderation": {"flagCount": 0}}

    def test_format_for_preloaded_annotation(self, formatter, group, flagged):
        annotation_resource = FakeAnnotationContext(flagged, group)

        formatter.preload([flagged.id])
        output = formatter.format(annotation_resource)
        assert output == {"moderation": {"flagCount": 2}}

    @pytest.fixture
    def user(self, factories):
        return factories.User()

    @pytest.fixture
    def group(self, factories):
        return factories.Group()

    @pytest.fixture
    def permission_granted(self, group):
        has_permission = FakePermissionCheck()
        has_permission.add_permission("moderate", group, True)
        return has_permission

    @pytest.fixture
    def permission_denied(self, group):
        has_permission = FakePermissionCheck()
        has_permission.add_permission("moderate", group, False)
        return has_permission

    @pytest.fixture
    def flagged(self, factories):
        annotation = factories.Annotation()
        factories.Flag.create_batch(2, annotation=annotation)
        return annotation

    @pytest.fixture
    def unflagged(self, factories):
        return factories.Annotation()

    @pytest.fixture
    def formatter(self, flag_count_svc, user, permission_granted):
        """A formatter with the most common configuration."""
        return AnnotationModerationFormatter(flag_count_svc, user, permission_granted)

    @pytest.fixture
    def flag_count_svc(self, db_session):
        return FlagCountService(db_session)
