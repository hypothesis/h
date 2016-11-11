# -*- coding: utf-8 -*-

import datetime

import pytest
import mock
from pyramid import httpexceptions
from webob.multidict import NestedMultiDict

from h.views import activity


@pytest.mark.usefixtures('paginate', 'query')
class TestSearch(object):
    def test_it_returns_404_when_feature_turned_off(self, pyramid_request):
        pyramid_request.feature.flags['search_page'] = False

        with pytest.raises(httpexceptions.HTTPNotFound):
            activity.search(pyramid_request)

    def test_it_checks_for_redirects(self, pyramid_request, query):
        activity.search(pyramid_request)

        query.check_url.assert_called_once_with(pyramid_request,
                                                query.extract.return_value)

    def test_it_executes_a_search_query(self, pyramid_request, query):
        activity.search(pyramid_request)

        query.execute.assert_called_once_with(pyramid_request,
                                              query.extract.return_value,
                                              page_size=activity.PAGE_SIZE)

    def test_it_allows_to_specify_the_page_size(self, pyramid_request, query):
        pyramid_request.params['page_size'] = 100
        activity.search(pyramid_request)

        query.execute.assert_called_once_with(pyramid_request,
                                              query.extract.return_value,
                                              page_size=100)

    def test_it_uses_default_page_size_when_value_is_a_string(self, pyramid_request, query):
        pyramid_request.params['page_size'] = 'foobar'
        activity.search(pyramid_request)

        query.execute.assert_called_once_with(pyramid_request,
                                              query.extract.return_value,
                                              page_size=activity.PAGE_SIZE)

    def test_it_uses_passed_in_page_size_for_pagination(self, pyramid_request, paginate):
        pyramid_request.params['page_size'] = 100
        activity.search(pyramid_request)

        paginate.assert_called_once_with(pyramid_request,
                                         mock.ANY,
                                         page_size=100)

    def test_it_returns_usernames(self, pyramid_request, query):
        """
        It should return a list of usernames to the template.

        query.execute() returns userids, search() should insert new values with
        just the username parts.

        """
        query.execute.return_value = mock.Mock(
            aggregations={
                'users': [
                    {'user': 'acct:test_user_1@hypothes.is'},
                    {'user': 'acct:test_user_2@hypothes.is'},
                    {'user': 'acct:test_user_3@hypothes.is'},
                ]
            }
        )

        result = activity.search(pyramid_request)

        usernames = [user['username']
                     for user in result['aggregations']['users']]
        assert usernames == ['test_user_1', 'test_user_2', 'test_user_3']

    def test_it_returns_userids(self, pyramid_request, query):
        """
        It should return a list of userids to the template.

        query.execute() returns userids as "user", search() should rename these
        to "userid".

        """
        query.execute.return_value = mock.Mock(
            aggregations={
                'users': [
                    {'user': 'acct:test_user_1@hypothes.is'},
                    {'user': 'acct:test_user_2@hypothes.is'},
                    {'user': 'acct:test_user_3@hypothes.is'},
                ]
            }
        )

        result = activity.search(pyramid_request)

        userids = [user['userid'] for user in result['aggregations']['users']]
        assert userids == [
            'acct:test_user_1@hypothes.is',
            'acct:test_user_2@hypothes.is',
            'acct:test_user_3@hypothes.is',
        ]

    def test_it_does_not_crash_if_there_are_no_users(self,
                                                     pyramid_request,
                                                     query):
        """
        It shouldn't crash if query.execute() returns no users.

        Sometimes there is no "users" key in the aggregations.

        """
        query.execute.return_value = mock.Mock(aggregations={})

        result = activity.search(pyramid_request)

        assert 'users' not in result['aggregations']

    def test_it_returns_group_suggestions(self,
                                          factories,
                                          pyramid_request,
                                          query):
        """It should return a list of group_suggestsions to the template."""
        fake_group_1 = factories.Group()
        fake_group_2 = factories.Group()
        fake_group_3 = factories.Group()
        pyramid_request.authenticated_user.groups = [
            fake_group_1, fake_group_2, fake_group_3]

        result = activity.search(pyramid_request)

        assert result['groups_suggestions'] == [
            {'name': fake_group_1.name, 'pubid': fake_group_1.pubid},
            {'name': fake_group_2.name, 'pubid': fake_group_2.pubid},
            {'name': fake_group_3.name, 'pubid': fake_group_3.pubid},
        ]

    @pytest.fixture
    def query(self, patch):
        return patch('h.views.activity.query')

    @pytest.fixture
    def paginate(self, patch):
        return patch('h.views.activity.paginate')

    @pytest.fixture
    def pyramid_request(self, factories, pyramid_request):
        pyramid_request.authenticated_user = factories.User()
        return pyramid_request


@pytest.mark.usefixtures('routes', 'search')
class TestGroupSearch(object):

    def test_it_returns_404_when_feature_turned_off(self,
                                                    group,
                                                    pyramid_request):
        pyramid_request.feature.flags['search_page'] = False

        for user in (None, group.creator, group.members[-1]):
            pyramid_request.authenticated_user = user
            with pytest.raises(httpexceptions.HTTPNotFound):
                activity.group_search(pyramid_request)

    def test_it_calls_search_with_the_request(self,
                                              group,
                                              pyramid_request,
                                              search):
        for user in (None, group.creator, group.members[-1]):
            pyramid_request.authenticated_user = user

            activity.group_search(pyramid_request)

            search.assert_called_once_with(pyramid_request)

            search.reset_mock()

    def test_it_just_returns_search_result_if_group_does_not_exist(
            self, group, pyramid_request, search):
        for user in (None, group.creator, group.members[-1]):
            pyramid_request.authenticated_user = user
            pyramid_request.matchdict['pubid'] = 'does_not_exist'

            assert activity.group_search(pyramid_request) == search.return_value

    def test_it_just_returns_search_result_if_user_not_logged_in(
            self, pyramid_request, search):
        pyramid_request.authenticated_user = None

        assert activity.group_search(pyramid_request) == search.return_value

    def test_it_just_returns_search_result_if_user_not_a_member_of_group(
            self, factories, pyramid_request, search):
        pyramid_request.authenticated_user = factories.User()

        assert activity.group_search(pyramid_request) == search.return_value

    def test_it_returns_group_info_if_user_a_member_of_group(self,
                                                             group,
                                                             pyramid_request):
        pyramid_request.authenticated_user = group.members[-1]

        group_info = activity.group_search(pyramid_request)['group']

        assert group_info['created'] == group.created.strftime('%B, %Y')
        assert group_info['description'] == group.description
        assert group_info['name'] == group.name
        assert group_info['pubid'] == group.pubid

    def test_it_checks_whether_the_user_has_admin_permission_on_the_group(
            self, group, pyramid_request):
        pyramid_request.authenticated_user = group.members[-1]

        activity.group_search(pyramid_request)

        pyramid_request.has_permission.assert_called_once_with('admin',
                                                               group)

    def test_it_does_not_show_the_edit_link_to_group_members(self,
                                                             group,
                                                             pyramid_request):
        pyramid_request.has_permission = mock.Mock(return_value=False)
        pyramid_request.authenticated_user = group.members[-1]

        result = activity.group_search(pyramid_request)

        assert 'group_edit_url' not in result

    def test_it_does_show_the_group_edit_link_to_group_creators(
            self, group, pyramid_request):
        pyramid_request.has_permission = mock.Mock(return_value=True)
        pyramid_request.authenticated_user = group.creator

        result = activity.group_search(pyramid_request)

        assert 'group_edit_url' in result

    def test_it_shows_the_more_info_version_of_the_page_if_more_info_is_in_the_request_params(
            self,
            group,
            pyramid_request):
        pyramid_request.authenticated_user = group.members[-1]
        pyramid_request.params['more_info'] = ''

        assert activity.group_search(pyramid_request)['more_info'] is True

    def test_it_shows_the_normal_version_of_the_page_if_more_info_is_not_in_the_request_params(
            self,
            group,
            pyramid_request):
        pyramid_request.authenticated_user = group.members[-1]

        assert activity.group_search(pyramid_request)['more_info'] is False

    def test_group_search_returns_pubid_in_opts(self, group, pyramid_request):
        result = activity.group_search(pyramid_request)
        assert result['opts']['search_groupname'] == group.pubid

    @pytest.fixture
    def pyramid_request(self, group, pyramid_request):
        pyramid_request.matchdict['pubid'] = group.pubid
        pyramid_request.authenticated_user = None
        pyramid_request.has_permission = mock.Mock(return_value=False)
        return pyramid_request

    @pytest.fixture
    def routes(self, pyramid_config):
        pyramid_config.add_route('group_read', '/groups/{pubid}/{slug}')
        pyramid_config.add_route('group_edit', '/groups/{pubid}/edit')


@pytest.mark.usefixtures('routes')
class TestSearchMoreInfo(object):

    def test_it_redirects_to_group_search(self, pyramid_request):
        """It should redirect and preserve the search query param."""
        pyramid_request.matchdict['pubid'] = 'test_pubid'
        pyramid_request.matched_route = mock.Mock()
        pyramid_request.matched_route.name = 'activity.group_search'
        pyramid_request.POST = {'q': 'foo bar', 'more_info': ''}

        result = activity.search_more_info(pyramid_request)

        assert isinstance(result, httpexceptions.HTTPSeeOther)
        assert result.location.startswith(
            'http://example.com/groups/test_pubid/search?')
        # The order of the params vary (because they're in an unordered dict)
        # but they should both be there.
        assert 'more_info=' in result.location
        assert 'q=foo+bar' in result.location

    def test_it_redirects_to_user_search(self, pyramid_request):
        """It should redirect and preserve the search query param."""
        pyramid_request.matchdict['username'] = 'test_username'
        pyramid_request.matched_route = mock.Mock()
        pyramid_request.matched_route.name = 'activity.user_search'
        pyramid_request.POST = {'q': 'foo bar', 'more_info': ''}

        result = activity.search_more_info(pyramid_request)

        assert isinstance(result, httpexceptions.HTTPSeeOther)
        assert result.location.startswith(
            'http://example.com/users/test_username/search?')
        # The order of the params vary (because they're in an unordered dict)
        # but they should both be there.
        assert 'more_info=' in result.location
        assert 'q=foo+bar' in result.location

    @pytest.fixture
    def routes(self, pyramid_config):
        pyramid_config.add_route('activity.group_search',
                                 '/groups/{pubid}/search')
        pyramid_config.add_route('activity.user_search',
                                 '/users/{username}/search')


@pytest.mark.usefixtures('routes')
class TestSearchBack(object):

    def test_it_redirects_to_group_search(self, pyramid_request):
        """It should redirect and preserve the search query param."""
        pyramid_request.matchdict['pubid'] = 'test_pubid'
        pyramid_request.matched_route = mock.Mock()
        pyramid_request.matched_route.name = 'activity.group_search'
        pyramid_request.POST = {'q': 'foo bar', 'back': ''}

        result = activity.search_back(pyramid_request)

        assert isinstance(result, httpexceptions.HTTPSeeOther)
        assert result.location == (
            'http://example.com/groups/test_pubid/search?q=foo+bar')

    def test_it_redirects_to_user_search(self, pyramid_request):
        """It should redirect and preserve the search query param."""
        pyramid_request.matchdict['username'] = 'test_username'
        pyramid_request.matched_route = mock.Mock()
        pyramid_request.matched_route.name = 'activity.user_search'
        pyramid_request.POST = {'q': 'foo bar', 'back': ''}

        result = activity.search_back(pyramid_request)

        assert isinstance(result, httpexceptions.HTTPSeeOther)
        assert result.location == (
            'http://example.com/users/test_username/search?q=foo+bar')

    @pytest.fixture
    def routes(self, pyramid_config):
        pyramid_config.add_route('activity.group_search',
                                 '/groups/{pubid}/search')
        pyramid_config.add_route('activity.user_search',
                                 '/users/{username}/search')


@pytest.mark.usefixtures('groups_service', 'routes')
class TestGroupLeave(object):

    def test_it_returns_404_when_feature_turned_off(self,
                                                    group,
                                                    pyramid_request):
        pyramid_request.feature.flags['search_page'] = False

        for user in (None, group.creator, group.members[-1]):
            pyramid_request.authenticated_user = user
            with pytest.raises(httpexceptions.HTTPNotFound):
                activity.group_leave(pyramid_request)

    def test_it_returns_404_when_the_group_does_not_exist(self,
                                                          pyramid_request):
        pyramid_request.params = NestedMultiDict({
            'group_leave': 'does_not_exist'})

        with pytest.raises(httpexceptions.HTTPNotFound):
            activity.group_leave(pyramid_request)

    def test_it_leaves_the_group(self,
                                 group,
                                 groups_service,
                                 pyramid_config,
                                 pyramid_request):
        pyramid_config.testing_securitypolicy(group.members[-1].userid)

        activity.group_leave(pyramid_request)

        groups_service.member_leave.assert_called_once_with(
            group, group.members[-1].userid)

    def test_it_redirects_to_the_search_page(self, group, pyramid_request):
        # This should be in the redirect URL.
        pyramid_request.POST = NestedMultiDict({'q': 'foo bar gar'})
        # This should *not* be in the redirect URL.
        pyramid_request.params = NestedMultiDict({'group_leave': group.pubid})
        result = activity.group_leave(pyramid_request)

        assert isinstance(result, httpexceptions.HTTPSeeOther)
        assert result.location == 'http://example.com/search?q=foo+bar+gar'

    @pytest.fixture
    def groups_service(self, patch, pyramid_config):
        groups_service = patch('h.groups.services.GroupsService')
        pyramid_config.register_service(groups_service, name='groups')
        return groups_service

    @pytest.fixture
    def pyramid_request(self, group, pyramid_request):
        pyramid_request.params = NestedMultiDict({'group_leave': group.pubid})
        return pyramid_request

    @pytest.fixture
    def routes(self, pyramid_config):
        pyramid_config.add_route('activity.search', '/search')


@pytest.mark.usefixtures('routes', 'search', 'user_service')
class TestUserSearch(object):
    def test_it_returns_404_when_feature_turned_off(self,
                                                    pyramid_request):
        pyramid_request.feature.flags['search_page'] = False

        with pytest.raises(httpexceptions.HTTPNotFound):
            activity.user_search(pyramid_request)

    def test_it_calls_search_with_request(self, pyramid_request, search):
        activity.user_search(pyramid_request)
        search.assert_called_once_with(pyramid_request)

    def test_it_returns_user_search_results(self,
                                            pyramid_request,
                                            search,
                                            user):
        results = activity.user_search(pyramid_request)
        assert results['opts']['search_username'] == user.username

    def test_it_shows_the_more_info_version_of_the_page_if_more_info_is_in_the_request_params(
            self,
            pyramid_request):
        pyramid_request.params['more_info'] = ''

        assert activity.user_search(pyramid_request)['more_info'] is True

    def test_it_shows_the_normal_version_of_the_page_if_more_info_is_not_in_the_request_params(
            self,
            pyramid_request):
        assert activity.user_search(pyramid_request)['more_info'] is False

    def test_it_fetches_the_user(self, pyramid_request, user, user_service):
        activity.user_search(pyramid_request)

        user_service.fetch.assert_called_once_with(user.username,
                                                   'example.com')

    def test_it_does_not_pass_user_to_template_if_user_does_not_exist(
            self, pyramid_request, user_service):
        user_service.fetch.return_value = None

        assert 'user' not in activity.user_search(pyramid_request)

    def test_it_passes_the_username_to_the_template_if_the_user_has_no_display_name(
            self, pyramid_request, user):
        user.display_name = None

        username = activity.user_search(pyramid_request)['user']['name']

        assert username == user.username

    def test_it_passes_the_display_name_to_the_template_if_the_user_has_one(
            self, pyramid_request, user):
        user.display_name = "Display Name"

        username = activity.user_search(pyramid_request)['user']['name']

        assert username == user.display_name

    def test_it_passes_the_num_annotations_to_the_template(self,
                                                           pyramid_request,
                                                           search):
        user_details = activity.user_search(pyramid_request)['user']

        assert user_details['num_annotations'] == search.return_value['total']

    def test_it_passes_the_other_user_details_to_the_template(self,
                                                              factories,
                                                              pyramid_request,
                                                              user_service):
        user = factories.User(
            registered_date=datetime.datetime(year=2016, month=8, day=1),
            uri='http://www.example.com/me',
            orcid='0000-0000-0000-0000',
        )
        user_service.fetch.return_value = user

        user_details = activity.user_search(pyramid_request)['user']

        assert user_details['description'] == user.description
        assert user_details['registered_date'] == 'August, 2016'
        assert user_details['location'] == user.location
        assert user_details['uri'] == user.uri
        assert user_details['domain'] == 'www.example.com'
        assert user_details['orcid'] == user.orcid

    def test_it_passes_the_edit_url_to_the_template(self,
                                                    pyramid_request,
                                                    user,
                                                    user_service):
        # The user whose page we're on is the same user as the authenticated
        # user.
        pyramid_request.authenticated_user = user
        user_service.fetch.return_value = user

        user_details = activity.user_search(pyramid_request)['user']

        assert user_details['edit_url'] == 'http://example.com/account/profile'

    def test_it_does_not_pass_the_edit_url_to_the_template(self,
                                                           factories,
                                                           pyramid_request,
                                                           user_service):
        # The user whose page we're on is *not* the same user as the
        # authenticated user.
        pyramid_request.authenticated_user = factories.User()
        user_service.fetch.return_value = factories.User()

        assert 'edit_url' not in activity.user_search(pyramid_request)['user']

    @pytest.fixture
    def pyramid_request(self, pyramid_request, user):
        pyramid_request.matchdict['username'] = user.username
        pyramid_request.authenticated_user = user
        return pyramid_request

    @pytest.fixture
    def routes(self, pyramid_config):
        pyramid_config.add_route('account_profile', '/account/profile')

    @pytest.fixture
    def user(self, factories):
        return factories.User()

    @pytest.fixture
    def user_service(self, pyramid_config, user):
        user_service = mock.Mock(spec_set=['fetch'])
        user_service.fetch.return_value = user
        pyramid_config.register_service(user_service, name='user')
        return user_service


@pytest.mark.usefixtures('routes', 'search')
class TestToggleUserFacet(object):

    def test_it_returns_404_when_feature_turned_off(self,
                                                    group,
                                                    pyramid_request):
        pyramid_request.feature.flags['search_page'] = False

        for user in (None, group.creator, group.members[-1]):
            pyramid_request.authenticated_user = user
            with pytest.raises(httpexceptions.HTTPNotFound):
                activity.toggle_user_facet(pyramid_request)

    def test_it_returns_a_redirect(self, pyramid_request):
        result = activity.toggle_user_facet(pyramid_request)

        assert isinstance(result, httpexceptions.HTTPSeeOther)

    def test_it_adds_the_user_facet_into_the_url(self, group, pyramid_request):
        result = activity.toggle_user_facet(pyramid_request)

        assert result.location == (
            'http://example.com/groups/{pubid}/search'
            '?q=user%3Afred'.format(pubid=group.pubid))

    def test_it_removes_the_user_facet_from_the_url(self,
                                                    group,
                                                    pyramid_request):
        pyramid_request.params['q'] = 'user:"fred"'

        result = activity.toggle_user_facet(pyramid_request)

        assert result.location == (
            'http://example.com/groups/{pubid}/search?q='.format(
                pubid=group.pubid))

    def test_it_preserves_query_when_adding_user_facet(self,
                                                       group,
                                                       pyramid_request):
        pyramid_request.params['q'] = 'foo bar'

        result = activity.toggle_user_facet(pyramid_request)

        assert result.location == (
            'http://example.com/groups/{pubid}/search'
            '?q=foo+bar+user%3Afred'.format(pubid=group.pubid))

    def test_it_preserves_query_when_removing_user_facet(self,
                                                         group,
                                                         pyramid_request):
        pyramid_request.params['q'] = 'user:"fred" foo bar'

        result = activity.toggle_user_facet(pyramid_request)

        assert result.location == (
            'http://example.com/groups/{pubid}/search'
            '?q=foo+bar'.format(pubid=group.pubid))

    @pytest.fixture
    def pyramid_request(self, group, pyramid_request):
        pyramid_request.feature.flags['search_page'] = True
        pyramid_request.params['toggle_user_facet'] = 'acct:fred@hypothes.is'
        pyramid_request.matchdict['pubid'] = group.pubid
        return pyramid_request

    @pytest.fixture
    def routes(self, pyramid_config):
        pyramid_config.add_route('activity.group_search',
                                 '/groups/{pubid}/search')


@pytest.fixture
def group(factories):
    # Create some other groups as well, just to make sure it gets the right
    # one from the db.
    factories.Group()
    factories.Group()

    group = factories.Group()
    group.members.extend([factories.User(), factories.User()])
    return group


@pytest.fixture
def pyramid_request(pyramid_request):
    pyramid_request.feature.flags['search_page'] = True
    return pyramid_request


@pytest.fixture
def search(patch):
    search = patch('h.views.activity.search')
    search.return_value = {
        'total': 200,
    }
    return search
