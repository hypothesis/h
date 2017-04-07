# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from collections import namedtuple

import pytest

from h.formatters.annotation_moderation import AnnotationModerationFormatter

FakeAnnotationResource = namedtuple('FakeAnnotationResource',
                                    ['annotation', 'group'])


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

    def test_preload_skipped_without_user(self, db_session):
        formatter = AnnotationModerationFormatter(db_session,
                                                  user=None,
                                                  has_permission=None)
        assert formatter.preload(['annotation-id']) is None

    def test_preload_skipped_without_ids(self, formatter):
        assert formatter.preload([]) is None

    def test_format_returns_empty_for_non_moderator(self, db_session, user, group, flagged, permission_denied):
        formatter = AnnotationModerationFormatter(db_session,
                                                  user,
                                                  permission_denied)
        annotation_resource = FakeAnnotationResource(flagged, group)

        assert formatter.format(annotation_resource) == {}

    def test_format_returns_flag_count_for_moderator(self, formatter, group, flagged):
        annotation_resource = FakeAnnotationResource(flagged, group)

        output = formatter.format(annotation_resource)
        assert output == {'moderation': {'flagCount': 2}}

    def test_format_returns_zero_flag_count(self, formatter, group, unflagged):
        annotation_resource = FakeAnnotationResource(unflagged, group)

        output = formatter.format(annotation_resource)
        assert output == {'moderation': {'flagCount': 0}}

    def test_format_for_preloaded_annotation(self, formatter, group, flagged):
        annotation_resource = FakeAnnotationResource(flagged, group)

        formatter.preload([flagged.id])
        output = formatter.format(annotation_resource)
        assert output == {'moderation': {'flagCount': 2}}

    @pytest.fixture
    def user(self, factories):
        return factories.User()

    @pytest.fixture
    def group(self, factories):
        return factories.Group()

    @pytest.fixture
    def permission_granted(self, group):
        has_permission = FakePermissionCheck()
        has_permission.add_permission('admin', group, True)
        return has_permission

    @pytest.fixture
    def permission_denied(self, group):
        has_permission = FakePermissionCheck()
        has_permission.add_permission('admin', group, False)
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
    def formatter(self, db_session, user, permission_granted):
        """A formatter with the most common configuration."""
        return AnnotationModerationFormatter(db_session,
                                             user,
                                             permission_granted)
