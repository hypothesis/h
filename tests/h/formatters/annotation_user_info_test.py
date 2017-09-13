# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from collections import namedtuple

import mock
import pytest

from h.formatters.annotation_user_info import AnnotationUserInfoFormatter

FakeAnnotationResource = namedtuple('FakeAnnotationResource', ['annotation'])


class TestAnnotationUserInfoFormatter(object):
    def test_preload_fetches_users_by_id(self, formatter, factories, user_svc):
        annotation_1 = factories.Annotation()
        annotation_2 = factories.Annotation()

        formatter.preload([annotation_1.id, annotation_2.id])

        user_svc.fetch_all.assert_called_once_with(
                set([annotation_1.userid, annotation_2.userid]))

    def test_preload_skips_fetching_for_empty_ids(self, formatter, user_svc):
        formatter.preload([])
        assert not user_svc.fetch_all.called

    def test_format_fetches_user_by_id(self, formatter, factories, user_svc):
        annotation = factories.Annotation.build()
        resource = FakeAnnotationResource(annotation)

        formatter.format(resource)

        user_svc.fetch.assert_called_once_with(annotation.userid)

    def test_format_returns_user_info_object(self, formatter, user_svc):
        user_svc.fetch.return_value = mock.Mock(display_name='Jane Doe')
        resource = FakeAnnotationResource(mock.Mock())

        result = formatter.format(resource)
        assert result == {'user_info': {'display_name': 'Jane Doe'}}

    def test_format_allows_null_display_name(self, formatter, user_svc):
        user_svc.fetch.return_value = mock.Mock(display_name=None)
        resource = FakeAnnotationResource(mock.Mock())

        result = formatter.format(resource)
        assert result == {'user_info': {'display_name': None}}

    def test_format_returns_empty_dict_when_user_missing(self, formatter, user_svc):
        user_svc.fetch.return_value = None
        resource = FakeAnnotationResource(mock.Mock())

        assert formatter.format(resource) == {}

    @pytest.fixture
    def formatter(self, db_session, user_svc):
        return AnnotationUserInfoFormatter(db_session, user_svc)

    @pytest.fixture
    def user_svc(self):
        return mock.Mock(spec_set=['fetch_all', 'fetch'])
