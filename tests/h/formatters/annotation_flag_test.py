# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from collections import namedtuple

import pytest

from h.formatters.annotation_flag import AnnotationFlagFormatter
from h.services.flag import FlagService

FakeAnnotationResource = namedtuple('FakeAnnotationResource', ['annotation'])


class TestAnnotationFlagFormatter(object):

    def test_format_for_existing_flag(self, formatter, factories, current_user):
        flag = factories.Flag(user=current_user)
        annotation_resource = FakeAnnotationResource(flag.annotation)
        assert formatter.format(annotation_resource) == {'flagged': True}

    def test_format_for_missing_flag(self, formatter, factories):
        annotation = factories.Annotation()
        annotation_resource = FakeAnnotationResource(annotation)

        assert formatter.format(annotation_resource) == {'flagged': False}

    def test_format_for_unauthenticated_user(self, flag_service, factories):
        annotation = factories.Annotation()
        annotation_resource = FakeAnnotationResource(annotation)
        formatter = AnnotationFlagFormatter(flag_service,
                                            user=None)

        assert formatter.format(annotation_resource) == {'flagged': False}

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
            current_user: factories.Flag.create_batch(3, user=current_user),
            other_user: factories.Flag.create_batch(2, user=other_user),
        }
