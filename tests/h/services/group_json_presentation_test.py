# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from h.services.group_json_presentation import GroupJSONPresentationService
from h.services.group_json_presentation import group_json_presentation_service_factory


class TestGroupJSONPresentationService(object):

    def test_present_proxies_to_presenter(self, svc, GroupJSONPresenter, factories):  # noqa: N803
        group = factories.Group()

        svc.present(group)

        GroupJSONPresenter.assert_called_once_with(group, svc.get_links)
        GroupJSONPresenter(group).asdict.assert_called_once()

    def test_present_all_proxies_to_presenter(self, svc, GroupsJSONPresenter, factories):  # noqa: N803
        groups = [factories.Group(), factories.Group()]

        svc.present_all(groups)

        GroupsJSONPresenter.assert_called_once_with(groups, svc.get_links)
        GroupsJSONPresenter(groups).asdicts.assert_called_once()

    def test_get_links_returns_group_url_if_same_authority(self, svc, factories, routes):
        group = factories.Group()

        links = svc.get_links(group)

        assert 'group' in links

    def test_get_links_returns_no_group_url_if_mismatched_authority(self, svc, factories, routes):
        group = factories.Group(authority='ding.com')

        links = svc.get_links(group)

        assert 'group' not in links


class TestGroupJSONPresentationFactory(object):

    def test_group_json_presentation_factory(self, pyramid_request):
        svc = group_json_presentation_service_factory(None, pyramid_request)

        assert isinstance(svc, GroupJSONPresentationService)


@pytest.fixture
def GroupJSONPresenter(patch):  # noqa: N802
    return patch('h.services.group_json_presentation.GroupJSONPresenter')


@pytest.fixture
def GroupsJSONPresenter(patch):  # noqa: N802
    return patch('h.services.group_json_presentation.GroupsJSONPresenter')


@pytest.fixture
def routes(pyramid_config):
    pyramid_config.add_route('group_read', '/g/{pubid}/{slug}')


@pytest.fixture
def svc(pyramid_request, db_session):
    return GroupJSONPresentationService(
        session=db_session,
        request_authority=pyramid_request.authority,
        route_url=pyramid_request.route_url
    )
