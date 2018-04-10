# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import mock
import pytest

from h.nipsa import search


@pytest.mark.usefixtures('group_service')
class TestFilter(object):
    def test_call_returns_nipsa_filter(self, pyramid_request, nipsa_filter):
        f = search.Filter(pyramid_request)

        assert f({}) == nipsa_filter.return_value

    def test_call_passes_group_service(self, pyramid_request, nipsa_filter, group_service):
        f = search.Filter(pyramid_request)

        f({})

        nipsa_filter.assert_called_once_with(group_service, mock.ANY)

    def test_call_passes_request_user(self, pyramid_request, nipsa_filter):
        f = search.Filter(pyramid_request)

        f({})

        nipsa_filter.assert_called_once_with(mock.ANY, pyramid_request.user)

    @pytest.fixture
    def group_service(self, pyramid_config):
        svc = mock.Mock()
        pyramid_config.register_service(svc, name='group')
        return svc

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.user = mock.Mock()
        return pyramid_request

    @pytest.fixture
    def nipsa_filter(self, patch):
        return patch('h.nipsa.search.nipsa_filter')


def test_nipsa_filter_filters_out_nipsad_annotations(group_service):
    """nipsa_filter() filters out annotations with "nipsa": True."""
    assert search.nipsa_filter(group_service) == {
        "bool": {
            "should": [
                {'not': {'term': {'nipsa': True}}},
                {'exists': {'field': 'thread_ids'}},
            ]
        }
    }


def test_nipsa_filter_users_own_annotations_are_not_filtered(group_service, user):
    filter_ = search.nipsa_filter(group_service, user)

    assert {'term': {'user': 'fred'}} in (
        filter_["bool"]["should"])


def test_nipsa_filter_coerces_userid_to_lowercase(group_service, user):
    user.userid = 'DonkeyNose'

    filter_ = search.nipsa_filter(group_service, user)

    assert {'term': {'user': 'donkeynose'}} in (
        filter_["bool"]["should"])


def test_nipsa_filter_group_annotations_not_filtered_for_creator(group_service, user):
    group_service.groupids_created_by.return_value = ['pubid-1', 'pubid-4', 'pubid-3']

    filter_ = search.nipsa_filter(group_service, user)

    assert {'terms': {'group': ['pubid-1', 'pubid-4', 'pubid-3']}} in (
        filter_['bool']['should'])


@pytest.fixture
def user():
    return mock.Mock(userid='fred')


@pytest.fixture
def group_service():
    svc = mock.Mock(spec_set=['groupids_created_by'])
    svc.groupids_created_by.return_value = []
    return svc
