# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from mock import Mock
from mock import PropertyMock
import pytest

from h.views import panels


@pytest.mark.usefixtures('routes')
class TestNavbar(object):
    def test_it_sets_null_username_when_logged_out(self, req):
        result = panels.navbar({}, req)
        assert result['username'] is None

    def test_it_sets_username_when_logged_in(self, req, authenticated_user):
        req.authenticated_user = authenticated_user
        result = panels.navbar({}, req)

        assert result['username'] == 'vannevar'

    def test_it_lists_groups_when_logged_in(self, req, authenticated_user):
        req.authenticated_user = authenticated_user
        result = panels.navbar({}, req)

        titles = [group.name for group in authenticated_user.groups]

        assert result['groups_menu_items'] == [
            {'title': titles[0], 'link': 'http://example.com/groups/id1/first'},
            {'title': titles[1], 'link': 'http://example.com/groups/id2/second'},
        ]

    def test_username_url_when_logged_in(self, req, authenticated_user):
        req.authenticated_user = authenticated_user
        result = panels.navbar({}, req)

        assert result['username_url'] == 'http://example.com/users/vannevar'

    def test_it_includes_search_query(self, req):
        req.params['q'] = 'tag:question'
        result = panels.navbar({}, req)

        assert result['q'] == 'tag:question'

    def test_it_includes_search_url_when_on_user_search(self, req):
        type(req.matched_route).name = PropertyMock(return_value='activity.user_search')
        req.matchdict = {'username': 'luke'}

        result = panels.navbar({}, req)
        assert result['search_url'] == 'http://example.com/users/luke'

    def test_it_includes_search_url_when_on_group_search(self, req):
        type(req.matched_route).name = PropertyMock(return_value='group_read')
        req.matchdict = {'pubid': 'foobar', 'slug': 'slugbar'}

        result = panels.navbar({}, req)
        assert result['search_url'] == 'http://example.com/groups/foobar/slugbar'

    def test_it_includes_default_search_url(self, req):
        result = panels.navbar({}, req)
        assert result['search_url'] == 'http://example.com/search'

    @pytest.fixture
    def routes(self, pyramid_config):
        pyramid_config.add_route('account', '/account')
        pyramid_config.add_route('account_profile', '/account/profile')
        pyramid_config.add_route('account_notifications', '/account/notifications')
        pyramid_config.add_route('account_developer', '/account/developer')
        pyramid_config.add_route('activity.search', '/search')
        pyramid_config.add_route('activity.user_search', '/users/{username}')
        pyramid_config.add_route('group_create', '/groups/new')
        pyramid_config.add_route('group_read', '/groups/:pubid/:slug')
        pyramid_config.add_route('logout', '/logout')

    @pytest.fixture
    def authenticated_user(self):
        groups = [
            Mock(pubid='id1', slug='first'),
            Mock(pubid='id2', slug='second'),
        ]
        authenticated_user = Mock(username='vannevar', groups=groups)
        return authenticated_user

    @pytest.fixture
    def req(self, pyramid_request):
        pyramid_request.authenticated_user = None
        return pyramid_request


@pytest.mark.usefixtures('routes')
class TestBackLink(object):

    def test_it_sets_back_location_from_referrer(self, pyramid_request):
        pyramid_request.referrer = 'https://example.com/prev-page'

        result = panels.back_link({}, pyramid_request)

        assert result['back_location'] == 'https://example.com/prev-page'

    @pytest.mark.parametrize('referrer,label', [
        ('https://example.com/users/currentuser', 'Back to your profile page'),
        ('https://example.com/users/currentuser?q=tag:foo', 'Back to your profile page'),
        ('https://example.com/users/otheruser', None),
        ('https://example.com/groups/abc/def', 'Back to group overview page'),
        ('https://example.com/search', None),
        (None, None),
    ])
    def test_it_sets_back_label(self, pyramid_request, referrer, label):
        pyramid_request.referrer = referrer

        result = panels.back_link({}, pyramid_request)

        assert result['back_label'] == label

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.authenticated_user = Mock(username='currentuser')
        return pyramid_request


@pytest.fixture
def routes(pyramid_config):
    pyramid_config.add_route('activity.user_search', '/users/{username}')
    pyramid_config.add_route('group_read', '/groups/{pubid}/{slug}')
    return pyramid_config
