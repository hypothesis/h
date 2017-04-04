# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from h.formatters.annotation_flag import AnnotationFlagFormatter
from h.services.flag import FlagService


class TestAnnotationFlagFormatter(object):
    def test_preload_sets_found_flags_to_true(self, flags, formatter, current_user):
        annotation_ids = [f.annotation_id for f in flags[current_user]]

        expected = {id_: True for id_ in annotation_ids}
        assert formatter.preload(annotation_ids) == expected

    def test_preload_sets_missing_flags_to_false(self, flags, formatter, other_user):
        annotation_ids = [f.annotation_id for f in flags[other_user]]

        expected = {id_: False for id_ in annotation_ids}
        assert formatter.preload(annotation_ids) == expected

    def test_format_for_existing_flag(self, formatter, factories, current_user):
        flag = factories.Flag(user=current_user)
        assert formatter.format(flag.annotation) == {'flagged': True}

    def test_format_for_missing_flag(self, formatter, factories):
        annotation = factories.Annotation()

        assert formatter.format(annotation) == {'flagged': False}

    def test_format_for_unauthenticated_user(self, db_session, factories):
        annotation = factories.Annotation()
        formatter = AnnotationFlagFormatter(db_session,
                                            user=None)

        assert formatter.format(annotation) == {'flagged': False}

    @pytest.fixture
    def current_user(self, factories):
        return factories.User()

    @pytest.fixture
    def other_user(self, factories):
        return factories.User()

    @pytest.fixture
    def formatter(self, flag_service, current_user):
        return AnnotationFlagFormatter(flag_service, current_user)

    @pytest.fixture
    def flag_service(self, db_session):
        return FlagService(db_session)

    @pytest.fixture
    def flags(self, factories, current_user, other_user):
        return {
            current_user: [factories.Flag(user=current_user) for _ in range(3)],
            other_user: [factories.Flag(user=other_user) for _ in range(2)],
        }
