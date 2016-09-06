# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from mock import Mock
from mock import PropertyMock
import pytest

from h.views import panels

@pytest.mark.usefixtures('routes')
def test_navbar_sets_null_username_when_logged_out(pyramid_request):
    pyramid_request.authenticated_user = None
    result = panels.navbar({}, pyramid_request)
    assert result['username'] == None


@pytest.mark.usefixtures('routes')
def test_navbar_sets_username_when_logged_in(pyramid_request, authenticated_user):
    pyramid_request.authenticated_user = authenticated_user
    result = panels.navbar({}, pyramid_request)

    assert result['username'] == 'vannevar'


@pytest.mark.usefixtures('routes')
def test_navbar_lists_groups_when_logged_in(pyramid_request, authenticated_user):
    pyramid_request.authenticated_user = authenticated_user
    result = panels.navbar({}, pyramid_request)

    titles = [group.name for group in authenticated_user.groups]

    assert result['groups_menu_items'] == [
        {'title': titles[0], 'link': 'http://example.com/groups/id1/first'},
        {'title': titles[1], 'link': 'http://example.com/groups/id2/second'},
    ]


@pytest.mark.usefixtures('routes')
def test_navbar_username_link_when_logged_in(pyramid_request, authenticated_user):
    pyramid_request.authenticated_user = authenticated_user
    result = panels.navbar({}, pyramid_request)

    assert result['username_link'] == 'http://example.com/search?q=user:vannevar'


@pytest.mark.usefixtures('routes')
def test_navbar_includes_search_query(pyramid_request):
    pyramid_request.authenticated_user = None
    pyramid_request.params['q'] = 'tag:question'
    result = panels.navbar({}, pyramid_request)

    assert result['q'] == 'tag:question'


@pytest.mark.usefixtures('routes')
def test_navbar_includes_search_url_when_on_user_search(pyramid_request):
    pyramid_request.authenticated_user = None

    type(pyramid_request.matched_route).name = PropertyMock(return_value='activity.user_search')
    pyramid_request.matchdict = {'username': 'luke'}

    result = panels.navbar({}, pyramid_request)
    assert result['search_link'] == 'http://example.com/users/luke/search'


@pytest.mark.usefixtures('routes')
def test_navbar_includes_search_url_when_on_group_search(pyramid_request):
    pyramid_request.authenticated_user = None

    type(pyramid_request.matched_route).name = PropertyMock(return_value='activity.group_search')
    pyramid_request.matchdict = {'pubid': 'foobar'}

    result = panels.navbar({}, pyramid_request)
    assert result['search_link'] == 'http://example.com/groups/foobar/search'


@pytest.mark.usefixtures('routes')
def test_navbar_includes_default_search_url(pyramid_request):
    pyramid_request.authenticated_user = None

    result = panels.navbar({}, pyramid_request)
    assert result['search_link'] == 'http://example.com/search'


@pytest.fixture
def routes(pyramid_config):
    pyramid_config.add_route('account', '/account')
    pyramid_config.add_route('account_profile', '/account/profile')
    pyramid_config.add_route('account_notifications', '/account/notifications')
    pyramid_config.add_route('account_developer', '/account/developer')
    pyramid_config.add_route('activity.search', '/search')
    pyramid_config.add_route('activity.user_search', '/users/{username}/search')
    pyramid_config.add_route('activity.group_search', '/groups/{pubid}/search')
    pyramid_config.add_route('group_create', '/groups/new')
    pyramid_config.add_route('group_read', '/groups/:pubid/:slug')
    pyramid_config.add_route('logout', '/logout')


@pytest.fixture
def authenticated_user():
    groups = [
        Mock(pubid='id1', slug='first'),
        Mock(pubid='id2', slug='second'),
    ]
    authenticated_user = Mock(username='vannevar', groups=groups)
    return authenticated_user
