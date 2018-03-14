# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime

import pytest
import mock
from pyramid import httpexceptions

from h.activity.query import ActivityResults
from h.views import activity


GROUP_TYPE_OPTIONS = ('group', 'open_group')


@pytest.mark.usefixtures('annotation_stats_service', 'paginate', 'query', 'routes')
class TestSearchController(object):

    def test_search_checks_for_redirects(self, controller, pyramid_request, query):
        controller.search()

        query.check_url.assert_called_once_with(pyramid_request,
                                                query.extract.return_value)

    def test_search_executes_a_search_query(self,
                                            controller,
                                            pyramid_request,
                                            query):
        controller.search()

        query.execute.assert_called_once_with(pyramid_request,
                                              query.extract.return_value,
                                              page_size=activity.PAGE_SIZE)

    def test_search_allows_to_specify_the_page_size(self,
                                                    controller,
                                                    pyramid_request,
                                                    query):
        pyramid_request.params['page_size'] = 100

        controller.search()

        query.execute.assert_called_once_with(pyramid_request,
                                              query.extract.return_value,
                                              page_size=100)

    def test_search_uses_default_page_size_when_value_is_a_string(self,
                                                                  controller,
                                                                  pyramid_request,
                                                                  query):
        pyramid_request.params['page_size'] = 'foobar'

        controller.search()

        query.execute.assert_called_once_with(pyramid_request,
                                              query.extract.return_value,
                                              page_size=activity.PAGE_SIZE)

    def test_search_uses_passed_in_page_size_for_pagination(self,
                                                            controller,
                                                            pyramid_request,
                                                            paginate):
        pyramid_request.params['page_size'] = 100

        controller.search()

        paginate.assert_called_once_with(pyramid_request,
                                         mock.ANY,
                                         page_size=100)

    def test_search_generates_tag_links(self, controller):
        result = controller.search()

        tag_link = result['tag_link']('foo')
        assert tag_link == 'http://example.com/search?q=tag%3Afoo'

    def test_search_generates_usernames(self, controller):
        result = controller.search()

        username = result['username_from_id']('acct:jim.smith@hypothes.is')
        assert username == 'jim.smith'

    def test_search_generates_username_links(self, controller):
        result = controller.search()

        user_link = result['user_link']('acct:jim.smith@hypothes.is')
        assert user_link == 'http://example.com/users/jim.smith'

    def test_search_returns_the_default_zero_message_to_the_template(self,
                                                                     controller):
        result = controller.search()

        assert result['zero_message'] == 'No annotations matched your search.'

    @pytest.fixture
    def controller(self, pyramid_request):
        return activity.SearchController(pyramid_request)

    @pytest.fixture
    def query(self, patch):
        return patch('h.views.activity.query')

    @pytest.fixture
    def paginate(self, patch):
        return patch('h.views.activity.paginate')

    @pytest.fixture
    def pyramid_request(self, factories, pyramid_request):
        pyramid_request.user = factories.User()
        return pyramid_request


@pytest.mark.usefixtures('annotation_stats_service', 'group_service', 'routes', 'search')
class TestGroupSearchController(object):

    """Tests unique to GroupSearchController."""

    def test_renders_join_template_when_no_read_permission(self, controller, pyramid_request, group):
        """When the request has no read permission but join, it should render the join template."""

        def fake_has_permission(permission, context=None):
            if permission == 'read':
                return False
            if permission == 'join':
                return True
        pyramid_request.has_permission = mock.Mock(side_effect=fake_has_permission)
        pyramid_request.override_renderer = mock.PropertyMock()

        result = controller.search()

        assert 'join.html' in pyramid_request.override_renderer
        assert result == {'group': group}

    def test_renders_join_template_when_not_logged_in(self, controller, factories, pyramid_request, group):
        """
        If user is logged out and has no read permission, prompt to login and join.
        """
        def fake_has_permission(permission, context=None):
            if permission in ('read', 'join'):
                return False
        pyramid_request.has_permission = mock.Mock(side_effect=fake_has_permission)

        result = controller.search()

        assert 'join.html' in pyramid_request.override_renderer
        assert result == {'group': group}

    @pytest.mark.parametrize('test_group,test_user', [('group', 'member')], indirect=['test_group', 'test_user'])
    def test_raises_not_found_when_no_read_or_join_permissions(self, controller, factories, pyramid_request, test_group, test_user):
        def fake_has_permission(permission, context=None):
            if permission in ('read', 'join'):
                return False
        pyramid_request.has_permission = mock.Mock(side_effect=fake_has_permission)

        with pytest.raises(httpexceptions.HTTPNotFound):
            controller.search()

    @pytest.mark.parametrize('test_group', GROUP_TYPE_OPTIONS, indirect=['test_group'])
    def test_search_redirects_if_slug_wrong(self,
                                            controller,
                                            test_group,
                                            pyramid_request):
        """
        If the slug in the URL is wrong it should redirect to the right one.

        For example /groups/<pubid>/foobar redirects to /groups/<pubid>/<slug>.

        The other 'group_read' views on h.views.groups do this, this tests that
        the ones in h.views.activity do as well.

        """
        pyramid_request.matchdict['slug'] = 'wrong'

        with pytest.raises(httpexceptions.HTTPMovedPermanently) as exc:
            controller.search()

        assert exc.value.location == '/groups/{pubid}/{slug}'.format(
            pubid=test_group.pubid, slug=test_group.slug)

    @pytest.mark.parametrize('test_group,test_user',
                             [('group', None), ('open_group', 'creator'), ('group', 'user')],
                             indirect=['test_group', 'test_user'])
    def test_search_calls_search_with_the_request(self,
                                                  controller,
                                                  factories,
                                                  test_group,
                                                  test_user,
                                                  pyramid_request,
                                                  search):
        controller.search()

        search.assert_called_once_with(controller)

        search.reset_mock()

    @pytest.mark.parametrize('test_group,test_user',
                             [('group', None), ('open_group', 'creator'), ('group', 'user')],
                             indirect=['test_group', 'test_user'])
    def test_search_just_returns_search_result_if_group_does_not_exist(
            self, controller, factories, test_group, test_user, pyramid_request, search):
        pyramid_request.matchdict['pubid'] = 'does_not_exist'

        assert controller.search() == search.return_value

    @pytest.mark.parametrize('test_group', GROUP_TYPE_OPTIONS, indirect=['test_group'])
    def test_search_just_returns_search_result_if_user_not_logged_in(
            self, controller, test_group, pyramid_request, search):
        assert controller.search() == search.return_value

    @pytest.mark.parametrize('test_group,test_user', [('group', 'user')], indirect=['test_group', 'test_user'])
    def test_search_just_returns_search_result_if_user_not_a_member_of_group(
            self, controller, test_group, test_user, factories, pyramid_request, search):

        assert controller.search() == search.return_value

    @pytest.mark.parametrize('test_group,test_user',
                             [('no_creator_group', 'member'), ('no_creator_open_group', 'user')],
                             indirect=['test_group', 'test_user'])
    def test_search_returns_group_info_if_group_creator_is_empty(self,
                                                                 controller,
                                                                 factories,
                                                                 test_group,
                                                                 test_user,
                                                                 pyramid_request):
        group_info = controller.search()['group']

        assert group_info['creator'] is None

    @pytest.mark.parametrize('test_group,test_user',
                             [('no_creator_group', 'member'), ('no_creator_open_group', 'user')],
                             indirect=['test_group', 'test_user'])
    def test_search_returns_group_info_if_user_has_read_permissions(self,
                                                                 controller,
                                                                 factories,
                                                                 test_group,
                                                                 test_user,
                                                                 pyramid_request):
        group_info = controller.search()['group']

        assert group_info['created'] == "{d:%B} {d.day}, {d:%Y}".format(d=test_group.created)
        assert group_info['description'] == test_group.description
        assert group_info['name'] == test_group.name
        assert group_info['pubid'] == test_group.pubid
        assert group_info['logo'] is None
        assert group_info['authority'] is None

    @pytest.mark.parametrize('test_group,test_user',
                             [('group', 'member'), ],
                             indirect=['test_group', 'test_user'])
    def test_search_returns_authority_and_logo_when_not_default_authority_and_logo_defined(self,
                                                     controller,
                                                     factories,
                                                     test_group,
                                                     test_user,
                                                     pyramid_request):
        group_info = controller.search()['group']

        assert group_info['logo'] == "biopub-logo"
        assert group_info['authority'] == "BIOPUB.HYPOTHES.IS"

    @pytest.mark.parametrize('test_group,test_user',
                             [('no_creator_group', 'member'), ('no_creator_open_group', 'user')],
                             indirect=['test_group', 'test_user'])
    def test_search_does_not_show_the_edit_link_to_non_admin_users(self,
                                                                   controller,
                                                                   factories,
                                                                   test_group,
                                                                   test_user,
                                                                   pyramid_request):
        def fake_has_permission(permission, context=None):
            return permission != 'admin'
        pyramid_request.has_permission = mock.Mock(side_effect=fake_has_permission)

        result = controller.search()

        assert 'group_edit_url' not in result

    @pytest.mark.parametrize('test_group,test_user',
                             [('open_group', 'creator'), ('group', 'creator')],
                             indirect=['test_group', 'test_user'])
    def test_search_does_show_the_group_edit_link_to_group_creators(self,
                                                                    controller,
                                                                    test_group,
                                                                    test_user,
                                                                    pyramid_request):
        pyramid_request.has_permission = mock.Mock(return_value=True)

        result = controller.search()

        assert 'group_edit_url' in result

    @pytest.mark.parametrize('test_group,test_user',
                             [('group', 'member')],
                             indirect=['test_group', 'test_user'])
    def test_search_shows_the_more_info_version_of_the_page_if_more_info_is_in_the_request_params(
            self,
            controller,
            factories,
            test_group,
            test_user,
            pyramid_request):
        pyramid_request.params['more_info'] = ''

        assert controller.search()['more_info'] is True

    @pytest.mark.parametrize('test_group,test_user',
                             [('group', 'member')],
                             indirect=['test_group', 'test_user'])
    def test_search_shows_the_normal_version_of_the_page_if_more_info_is_not_in_the_request_params(
            self,
            controller,
            factories,
            test_group,
            test_user,
            pyramid_request):

        assert controller.search()['more_info'] is False

    @pytest.mark.parametrize('test_group', GROUP_TYPE_OPTIONS, indirect=['test_group'])
    def test_search_returns_name_in_opts(self,
                                         controller,
                                         test_group,
                                         pyramid_request):
        result = controller.search()

        assert result['opts']['search_groupname'] == test_group.name

    @pytest.mark.parametrize('test_group,test_user',
                             [('group', 'member'), ('open_group', 'user')],
                             indirect=['test_group', 'test_user'])
    def test_search_returns_group_creator(self,
                                          controller,
                                          factories,
                                          pyramid_request,
                                          test_user,
                                          test_group):
        result = controller.search()

        assert result['group']['creator'] == test_group.creator.userid

    @pytest.mark.parametrize('test_group,test_user', [('group', 'member')], indirect=['test_group', 'test_user'])
    def test_search_returns_group_members_usernames(self,
                                                    controller,
                                                    pyramid_request,
                                                    test_user,
                                                    test_group):
        result = controller.search()

        actual = set([m['username'] for m in result['group']['members']])
        expected = set([m.username for m in test_group.members])
        assert actual == expected

    @pytest.mark.parametrize('test_group,test_user', [('group', 'member')], indirect=['test_group', 'test_user'])
    def test_search_returns_group_members_userid(self,
                                                 controller,
                                                 pyramid_request,
                                                 test_user,
                                                 test_group):
        result = controller.search()

        actual = set([m['userid'] for m in result['group']['members']])
        expected = set([m.userid for m in test_group.members])
        assert actual == expected

    @pytest.mark.parametrize('test_group,test_user', [('group', 'member')], indirect=['test_group', 'test_user'])
    def test_search_returns_group_members_faceted_by(self,
                                                     controller,
                                                     pyramid_request,
                                                     test_user,
                                                     test_group):
        faceted_user = test_group.members[0]
        pyramid_request.params = {'q': 'user:%s' % test_group.members[0].username}

        result = controller.search()

        for member in result['group']['members']:
            assert member['faceted_by'] is (member['userid'] == faceted_user.userid)

    def test_search_returns_annotation_count_for_group_members(self,
                                                               controller,
                                                               pyramid_request,
                                                               group,
                                                               search,
                                                               factories):
        user_1 = factories.User()
        user_2 = factories.User()
        group.members = [user_1, user_2]

        pyramid_request.user = group.members[-1]

        counts = {user_1.userid: 24, user_2.userid: 6}
        users_aggregation = [
            {'user': user_1.userid, 'count': counts[user_1.userid]},
            {'user': user_2.userid, 'count': counts[user_2.userid]},
        ]
        search.return_value = {
            'search_results': ActivityResults(total=200,
                                              aggregations={'users': users_aggregation},
                                              timeframes=[]),
        }

        result = controller.search()

        for member in result['group']['members']:
            assert member['count'] == counts[member['userid']]

    @pytest.mark.parametrize('test_group,test_user',
                             [('open_group', 'user')],
                             indirect=['test_group', 'test_user'])
    def test_search_returns_group_moderators_usernames(self,
                                                       controller,
                                                       factories,
                                                       pyramid_request,
                                                       test_user,
                                                       test_group):
        result = controller.search()

        actual = set([m['username'] for m in result['group']['moderators']])
        expected = set([test_group.creator.username])
        assert actual == expected

    @pytest.mark.parametrize('test_group,test_user',
                             [('open_group', 'user')],
                             indirect=['test_group', 'test_user'])
    def test_search_returns_group_moderators_userid(self,
                                                    controller,
                                                    factories,
                                                    pyramid_request,
                                                    test_user,
                                                    test_group):
        result = controller.search()

        actual = set([m['userid'] for m in result['group']['moderators']])
        expected = set([test_group.creator.userid])
        assert actual == expected

    @pytest.mark.parametrize('test_group,test_user',
                             [('open_group', 'user')],
                             indirect=['test_group', 'test_user'])
    def test_search_returns_group_moderators_faceted_by(self,
                                                        controller,
                                                        factories,
                                                        pyramid_request,
                                                        test_user,
                                                        test_group):
        pyramid_request.params = {'q': 'user:%s' % "does_not_matter"}

        result = controller.search()
        assert result['group']['members'] is None, "Open group search should return members=None."
        for moderator in result['group']['moderators']:
            assert not moderator['faceted_by']

    @pytest.mark.parametrize('test_group,test_user',
                             [('open_group', 'user')],
                             indirect=['test_group', 'test_user'])
    def test_search_returns_annotation_count_for_group_moderators(self,
                                                                  controller,
                                                                  pyramid_request,
                                                                  test_group,
                                                                  test_user,
                                                                  search,
                                                                  factories):
        user_1 = test_group.creator
        user_2 = factories.User()

        counts = {user_1.userid: 24, user_2.userid: 6}
        users_aggregation = [
            {'user': user_1.userid, 'count': counts[user_1.userid]},
            {'user': user_2.userid, 'count': counts[user_2.userid]},
        ]
        search.return_value = {
            'search_results': ActivityResults(total=200,
                                              aggregations={'users': users_aggregation},
                                              timeframes=[]),
        }

        result = controller.search()
        for moderator in result['group']['moderators']:
            assert moderator['count'] == counts[moderator['userid']]

    @pytest.mark.parametrize('test_group,test_user',
                             [('open_group', 'user'), ('group', 'user')],
                             indirect=['test_group', 'test_user'])
    def test_search_returns_the_default_zero_message_to_the_template(
            self, controller, factories, test_group, test_user, pyramid_request, search):
        """If there's a non-empty query it uses the default zero message."""
        search.return_value['q'] = 'foo'

        result = controller.search()

        assert result['zero_message'] == 'No annotations matched your search.'

    @pytest.mark.parametrize('test_group,test_user',
                             [('open_group', 'user'), ('group', 'member')],
                             indirect=['test_group', 'test_user'])
    def test_search_returns_the_group_zero_message_to_the_template(
            self, controller, factories, test_group, test_user, pyramid_request, search):
        """If the query is empty it overrides the default zero message."""
        search.return_value['q'] = ''

        result = controller.search()

        assert result['zero_message'] == (
            "The group “{name}” has not made any annotations yet.".format(
                name=test_group.name))

    @pytest.mark.parametrize('test_group,test_user', [('group', 'member')], indirect=['test_group', 'test_user'])
    def test_leave_leaves_the_group(self,
                                    controller,
                                    test_group,
                                    test_user,
                                    group_leave_request,
                                    group_service,
                                    pyramid_request,
                                    pyramid_config):
        pyramid_config.testing_securitypolicy(test_user.userid)

        controller.leave()

        group_service.member_leave.assert_called_once_with(
            test_group, test_user.userid)

    def test_leave_redirects_to_the_search_page(self,
                                                controller,
                                                group,
                                                group_leave_request):
        # This should be in the redirect URL.
        group_leave_request.POST['q'] = 'foo bar gar'
        # This should *not* be in the redirect URL.
        group_leave_request.POST['group_leave'] = group.pubid

        result = controller.leave()

        assert isinstance(result, httpexceptions.HTTPSeeOther)
        assert result.location == 'http://example.com/search?q=foo+bar+gar'

    def test_join_raises_not_found_when_not_joinable(self, controller, pyramid_request, group):
        pyramid_request.has_permission = mock.Mock(return_value=False)

        with pytest.raises(httpexceptions.HTTPNotFound):
            controller.join()

    def test_join_adds_group_member(self, controller, group, pyramid_request, pyramid_config, group_service):
        pyramid_config.testing_securitypolicy('acct:doe@example.org')

        controller.join()

        group_service.member_join.assert_called_once_with(group, 'acct:doe@example.org')

    @pytest.mark.parametrize('test_group', GROUP_TYPE_OPTIONS, indirect=['test_group'])
    def test_join_redirects_to_search_page(self, controller, test_group, pyramid_request):
        # Although open groups aren't joinable they still have a share link that looks the same.
        result = controller.join()

        assert isinstance(result, httpexceptions.HTTPSeeOther)
        expected = pyramid_request.route_url('group_read', pubid=test_group.pubid, slug=test_group.slug)
        assert result.location == expected

    @pytest.mark.parametrize('test_group,test_user',
                             [('group', 'member'), ('open_group', 'user')],
                             indirect=['test_group', 'test_user'])
    def test_search_passes_the_group_annotation_count_to_the_template(self,
                                                                      controller,
                                                                      factories,
                                                                      test_group,
                                                                      test_user,
                                                                      pyramid_request):
        result = controller.search()['stats']
        assert result['annotation_count'] == 5

    @pytest.mark.parametrize('q,test_group', [('', 'open_group'), ('   ', 'group')], indirect=['test_group'])
    def test_leave_removes_empty_query_from_url(self,
                                                controller,
                                                test_group,
                                                pyramid_request,
                                                group_leave_request,
                                                q):
        """
        It should remove an empty q from the URL it redirects to.

        We don't want to redirect to a URL with a pointless trailing empty ?q=.

        """
        group_leave_request.POST['q'] = q
        group_leave_request.POST['group_leave'] = test_group.pubid

        result = controller.leave()

        assert isinstance(result, httpexceptions.HTTPSeeOther)
        assert result.location == 'http://example.com/search'

    @pytest.mark.parametrize('test_group', GROUP_TYPE_OPTIONS, indirect=['test_group'])
    def test_back_redirects_to_group_search(self,
                                            controller,
                                            test_group,
                                            pyramid_request):
        """It should redirect and preserve the search query param."""
        pyramid_request.matched_route = mock.Mock()
        pyramid_request.matched_route.name = 'group_read'
        pyramid_request.params = {'q': 'foo bar', 'back': ''}

        result = controller.back()

        assert isinstance(result, httpexceptions.HTTPSeeOther)
        assert result.location == (
            'http://example.com/groups/{pubid}/{slug}?q=foo+bar'.format(
                pubid=test_group.pubid, slug=test_group.slug))

    @pytest.mark.parametrize('test_group', GROUP_TYPE_OPTIONS, indirect=['test_group'])
    @pytest.mark.usefixtures('toggle_user_facet_request')
    def test_toggle_user_facet_returns_a_redirect(self, controller, test_group):
        result = controller.toggle_user_facet()

        assert isinstance(result, httpexceptions.HTTPSeeOther)

    @pytest.mark.parametrize('test_group', GROUP_TYPE_OPTIONS, indirect=['test_group'])
    @pytest.mark.usefixtures('toggle_user_facet_request')
    def test_toggle_user_facet_adds_the_user_facet_into_the_url(self,
                                                                controller,
                                                                pyramid_request,
                                                                test_group):
        result = controller.toggle_user_facet()

        assert result.location == (
            'http://example.com/groups/{pubid}/{slug}'
            '?q=user%3Afred'.format(pubid=test_group.pubid, slug=test_group.slug))

    @pytest.mark.parametrize('test_group', GROUP_TYPE_OPTIONS, indirect=['test_group'])
    def test_toggle_user_facet_removes_the_user_facet_from_the_url(self,
                                                                   controller,
                                                                   test_group,
                                                                   pyramid_request,
                                                                   toggle_user_facet_request):
        toggle_user_facet_request.params['q'] = 'user:"fred"'

        result = controller.toggle_user_facet()

        assert result.location == (
            'http://example.com/groups/{pubid}/{slug}'.format(
                pubid=test_group.pubid, slug=test_group.slug))

    @pytest.mark.parametrize('test_group', GROUP_TYPE_OPTIONS, indirect=['test_group'])
    def test_toggle_user_facet_preserves_query_when_adding_user_facet(self,
                                                                      controller,
                                                                      test_group,
                                                                      pyramid_request,
                                                                      toggle_user_facet_request):
        toggle_user_facet_request.params['q'] = 'foo bar'

        result = controller.toggle_user_facet()

        assert result.location == (
            'http://example.com/groups/{pubid}/{slug}'
            '?q=foo+bar+user%3Afred'.format(pubid=test_group.pubid, slug=test_group.slug))

    @pytest.mark.parametrize('test_group', GROUP_TYPE_OPTIONS, indirect=['test_group'])
    def test_toggle_user_facet_preserves_query_when_removing_user_facet(self,
                                                                        controller,
                                                                        test_group,
                                                                        pyramid_request,
                                                                        toggle_user_facet_request):
        toggle_user_facet_request.params['q'] = 'user:"fred" foo bar'

        result = controller.toggle_user_facet()

        assert result.location == (
            'http://example.com/groups/{pubid}/{slug}'
            '?q=foo+bar'.format(pubid=test_group.pubid, slug=test_group.slug))

    @pytest.mark.parametrize('test_group', GROUP_TYPE_OPTIONS, indirect=['test_group'])
    def test_toggle_user_facet_preserves_query_when_removing_one_of_multiple_username_facets(
            self, controller, test_group, pyramid_request, toggle_user_facet_request):
        toggle_user_facet_request.params['q'] = 'user:"foo" user:"fred" user:"bar"'

        result = controller.toggle_user_facet()

        assert result.location == (
            'http://example.com/groups/{pubid}/{slug}'
            '?q=user%3Afoo+user%3Abar'.format(pubid=test_group.pubid, slug=test_group.slug))

    @pytest.mark.parametrize('q,test_group', [('user:fred', 'open_group'), ('  user:fred   ', 'group')], indirect=['test_group'])
    def test_toggle_user_facet_removes_empty_query(self,
                                                   controller,
                                                   test_group,
                                                   pyramid_request,
                                                   toggle_user_facet_request,
                                                   q):
        """
        It should remove an empty query from the URL.

        We don't want to redirect to a URL with a pointless trailing empty ?q=.

        """
        toggle_user_facet_request.params['q'] = q

        result = controller.toggle_user_facet()

        assert result.location == (
            'http://example.com/groups/{pubid}/{slug}'.format(
                pubid=test_group.pubid, slug=test_group.slug))

    @pytest.fixture(scope='function')
    def test_group(self, request, groups):
        return groups[request.param]

    @pytest.fixture(scope='function')
    def test_user(self, request, users):
        # Since open groups don't have members we only eval this
        # if member was specifically requested.
        if request.param == "member":
            return request.getfixturevalue('test_group').members[-1]
        return users[request.param]

    @pytest.fixture
    def users(self, request, user, factories):
        group = request.getfixturevalue('test_group')
        return {None: None,
                "creator": group.creator,
                "user": factories.User()}

    @pytest.fixture
    def controller(self, request, group, pyramid_request):
        test_group = group
        if 'test_group' in request.fixturenames:
            test_group = request.getfixturevalue('test_group')
        return activity.GroupSearchController(test_group, pyramid_request)

    @pytest.fixture
    def group_leave_request(self, request, group, pyramid_request):
        test_group = group
        if 'test_group' in request.fixturenames:
            test_group = request.getfixturevalue('test_group')
        pyramid_request.POST = {'group_leave': test_group.pubid}
        return pyramid_request

    @pytest.fixture
    def group_service(self, patch, pyramid_config):
        group_service = patch('h.services.group.GroupService')
        pyramid_config.register_service(group_service, name='group')
        return group_service

    @pytest.fixture
    def pyramid_request(self, request, group, pyramid_request):
        test_group = group
        if 'test_group' in request.fixturenames:
            test_group = request.getfixturevalue('test_group')
        pyramid_request.matchdict['pubid'] = test_group.pubid
        pyramid_request.matchdict['slug'] = test_group.slug
        pyramid_request.user = None
        if 'test_user' in request.fixturenames:
            pyramid_request.user = request.getfixturevalue('test_user')
        return pyramid_request

    @pytest.fixture
    def toggle_user_facet_request(self, pyramid_request):
        pyramid_request.params['toggle_user_facet'] = 'acct:fred@hypothes.is'
        return pyramid_request


@pytest.mark.usefixtures('annotation_stats_service', 'user_service', 'routes', 'search')
class TestUserSearchController(object):

    """Tests unique to UserSearchController."""

    def test_search_calls_search_with_request(self,
                                              controller,
                                              pyramid_request,
                                              search):
        controller.search()

        search.assert_called_once_with(controller)

    def test_search_returns_user_search_results(self, controller, user):
        results = controller.search()

        assert results['opts']['search_username'] == user.username

    def test_search_shows_the_more_info_version_of_the_page_if_more_info_is_in_the_request_params(
            self, controller, pyramid_request):
        pyramid_request.params['more_info'] = ''

        assert controller.search()['more_info'] is True

    def test_search_shows_the_normal_version_of_the_page_if_more_info_is_not_in_the_request_params(
            self, controller):
        assert controller.search()['more_info'] is False

    def test_search_passes_the_username_to_the_template_if_the_user_has_no_display_name(
            self, controller, user):
        user.display_name = None

        username = controller.search()['user']['name']

        assert username == user.username

    def test_search_passes_the_display_name_to_the_template_if_the_user_has_one(
            self, controller, user):
        user.display_name = "Display Name"

        username = controller.search()['user']['name']

        assert username == user.display_name

    def test_search_passes_the_user_annotation_counts_to_the_template(self,
                                                                      controller,
                                                                      pyramid_config,
                                                                      user):
        pyramid_config.testing_securitypolicy(user.userid)

        stats = controller.search()['stats']

        assert stats['annotation_count'] == 6

    def test_search_passes_public_annotation_counts_to_the_template(self,
                                                                    controller,
                                                                    factories,
                                                                    pyramid_config,
                                                                    pyramid_request):
        """
        The annotation count passed to the view should not include private and group annotation counts
        if the user whose page we are on is different from the authenticated user.

        """
        pyramid_config.testing_securitypolicy(factories.User().userid)

        stats = controller.search()['stats']

        assert stats['annotation_count'] == 1

    def test_search_passes_the_other_user_details_to_the_template(self,
                                                                  controller,
                                                                  factories,
                                                                  user):
        user_details = controller.search()['user']

        assert user_details['description'] == user.description
        assert user_details['registered_date'] == 'August 1, 2016'
        assert user_details['location'] == user.location
        assert user_details['uri'] == user.uri
        assert user_details['domain'] == 'www.example.com'
        assert user_details['orcid'] == user.orcid

    def test_search_passes_the_edit_url_to_the_template(self,
                                                        controller,
                                                        user):
        # The user whose page we're on is the same user as the authenticated
        # user.
        pyramid_request.user = user

        user_details = controller.search()['user']

        assert user_details['edit_url'] == 'http://example.com/account/profile'

    def test_search_does_not_pass_the_edit_url_to_the_template(self,
                                                               controller,
                                                               factories,
                                                               pyramid_request):
        # The user whose page we're on is *not* the same user as the
        # authenticated user.
        pyramid_request.user = factories.User()

        assert 'edit_url' not in controller.search()['user']

    def test_search_returns_the_default_zero_message_to_the_template(
            self, controller, search):
        """If there's a non-empty query it uses the default zero message."""
        search.return_value['q'] = 'foo'

        result = controller.search()

        assert result['zero_message'] == 'No annotations matched your search.'

    def test_search_returns_the_user_zero_message_to_the_template(
            self, controller, factories, pyramid_request, search, user):
        """If the query is empty it overrides the default zero message."""
        pyramid_request.user = factories.User()
        search.return_value['q'] = ''

        result = controller.search()

        assert result['zero_message'] == (
            '{name} has not made any annotations yet.'.format(
                name=user.username))

    def test_search_shows_the_getting_started_box_when_on_your_own_page(
            self, controller, search, user):
        search.return_value['q'] = ''

        result = controller.search()

        assert result['zero_message'] == '__SHOW_GETTING_STARTED__'

    def test_back_redirects_to_user_search(self,
                                           controller,
                                           user,
                                           pyramid_request):
        """It should redirect and preserve the search query param."""
        pyramid_request.matched_route = mock.Mock()
        pyramid_request.matched_route.name = 'activity.user_search'
        pyramid_request.params = {'q': 'foo bar', 'back': ''}

        result = controller.back()

        assert isinstance(result, httpexceptions.HTTPSeeOther)
        assert result.location == (
            'http://example.com/users/{username}?q=foo+bar'.format(
                username=user.username))

    @pytest.mark.parametrize('q', ['', '   '])
    def test_back_removes_empty_query(self,
                                      controller,
                                      user,
                                      pyramid_request,
                                      q):
        """
        It should remove an empty q param from the URL.

        We don't want to redirect to a URL with a pointless trailing empty ?q=.

        """
        pyramid_request.matched_route = mock.Mock()
        pyramid_request.matched_route.name = 'activity.user_search'
        pyramid_request.params = {'q': q, 'back': ''}

        result = controller.back()

        assert isinstance(result, httpexceptions.HTTPSeeOther)
        assert result.location == (
            'http://example.com/users/{username}'.format(
                username=user.username))

    @pytest.fixture
    def controller(self, user, pyramid_request):
        return activity.UserSearchController(user, pyramid_request)

    @pytest.fixture
    def pyramid_request(self, pyramid_request, user):
        pyramid_request.matchdict['username'] = user.username
        pyramid_request.user = user
        return pyramid_request

    @pytest.fixture
    def user(self, factories):
        return factories.User(
            registered_date=datetime.datetime(year=2016, month=8, day=1),
            uri='http://www.example.com/me',
            orcid='0000-0000-0000-0000',
        )

    @pytest.fixture
    def user_service(self, patch, pyramid_config):
        user_service = patch('h.services.user.UserService')
        pyramid_config.register_service(user_service, name='user')
        return user_service


@pytest.mark.usefixtures('routes', 'search')
class TestGroupAndUserSearchController(object):

    """Tests common to both GroupSearchController and UserSearchController."""

    @pytest.mark.usefixtures('delete_lozenge_request')
    def test_delete_lozenge_returns_a_redirect(self, controller):
        result = controller.delete_lozenge()

        assert isinstance(result, httpexceptions.HTTPSeeOther)

        # This tests that the location redirected to is correct and also that
        # the delete_lozenge param has been removed (and is not part of the
        # URL).
        assert result.location == 'http://example.com/search'

    def test_delete_lozenge_preserves_the_query_param(self,
                                                      controller,
                                                      delete_lozenge_request):
        delete_lozenge_request.params['q'] = 'foo bar'

        location = controller.delete_lozenge().location

        location == 'http://example.com/search?q=foo+bar'

    @pytest.mark.parametrize('q', ['', '   '])
    def test_delete_lozenge_removes_empty_queries(self,
                                                  controller,
                                                  delete_lozenge_request,
                                                  q):
        """
        It should remove an empty q from the URL.

        We don't want to redirect to a URL with a pointless trailing empty ?q=.

        """
        delete_lozenge_request.params['q'] = q

        location = controller.delete_lozenge().location

        location == 'http://example.com/search'

    @pytest.mark.usefixtures('toggle_tag_facet_request')
    def test_toggle_tag_facet_returns_a_redirect(self, controller):
        result = controller.toggle_tag_facet()

        assert isinstance(result, httpexceptions.HTTPSeeOther)

    @pytest.mark.usefixtures('toggle_tag_facet_request')
    def test_toggle_tag_facet_adds_the_tag_facet_into_the_url(self,
                                                              controller):
        result = controller.toggle_tag_facet()

        assert result.location == 'http://example.com/users/foo?q=tag%3Agar'

    def test_toggle_tag_facet_removes_the_tag_facet_from_the_url(
            self, controller, toggle_tag_facet_request):
        toggle_tag_facet_request.params['q'] = 'tag:"gar"'

        result = controller.toggle_tag_facet()

        assert result.location == 'http://example.com/users/foo'

    def test_toggle_tag_facet_preserves_query_when_adding_tag_facet(
            self, controller, toggle_tag_facet_request):
        toggle_tag_facet_request.params['q'] = 'foo bar'

        result = controller.toggle_tag_facet()

        assert result.location == (
            'http://example.com/users/foo?q=foo+bar+tag%3Agar')

    def test_toggle_tag_facet_preserves_query_when_removing_tag_facet(
            self, controller, toggle_tag_facet_request):
        toggle_tag_facet_request.params['q'] = 'tag:"gar" foo bar'

        result = controller.toggle_tag_facet()

        assert result.location == 'http://example.com/users/foo?q=foo+bar'

    def test_toggle_tag_facet_preserves_query_when_removing_one_of_multiple_tag_facets(
            self, controller, toggle_tag_facet_request):
        toggle_tag_facet_request.params['q'] = 'tag:"foo" tag:"gar" tag:"bar"'

        result = controller.toggle_tag_facet()

        assert result.location == (
            'http://example.com/users/foo?q=tag%3Afoo+tag%3Abar')

    @pytest.mark.parametrize('q', ['tag:gar', ' tag:gar   '])
    def test_toggle_tag_facet_removes_empty_query(self,
                                                  controller,
                                                  toggle_tag_facet_request,
                                                  q):
        """
        It should remove an empty q from the URL.


        We don't want to redirect to a URL with a pointless trailing empty ?q=.

        """
        toggle_tag_facet_request.params['q'] = q

        result = controller.toggle_tag_facet()

        assert result.location == 'http://example.com/users/foo'

    @pytest.fixture(params=['user_search_controller', 'group_search_controller'])
    def controller(self, request):
        """
        Return a UserSearchController and a GroupSearchController.
        Any test that uses this fixture will be called twice - once with a
        UserSearchController instance as the controller argument, and once with
        a GroupSearchController.
        """
        return request.getfuncargvalue(request.param)

    @pytest.fixture
    def group_search_controller(self, group, pyramid_request):
        # Set the slug in the URL to the slug of the group.
        # Otherwise GroupSearchController will redirect the request to the
        # correct URL.
        pyramid_request.matchdict['slug'] = group.slug

        return activity.GroupSearchController(group, pyramid_request)

    @pytest.fixture
    def delete_lozenge_request(self, pyramid_request):
        pyramid_request.params['delete_lozenge'] = ''
        return pyramid_request

    @pytest.fixture
    def toggle_tag_facet_request(self, pyramid_request):
        pyramid_request.matched_route = mock.Mock()
        pyramid_request.matched_route.name = 'activity.user_search'
        pyramid_request.params['toggle_tag_facet'] = 'gar'
        pyramid_request.matchdict['username'] = 'foo'
        return pyramid_request

    @pytest.fixture
    def user_search_controller(self, user, pyramid_request):
        return activity.UserSearchController(user, pyramid_request)


class FakeAnnotationStatsService(object):
    def user_annotation_counts(self, userid):
        return {'public': 1, 'private': 3, 'group': 2, 'total': 6}

    def group_annotation_count(self, pubid):
        return 5


@pytest.fixture
def group(factories):
    group = factories.Group()
    group.members.extend([factories.User(), factories.User()])
    group.authority = "biopub.hypothes.is"
    return group


@pytest.fixture
def no_creator_group(factories):
    group = factories.Group()
    group.creator = None
    group.members.extend([factories.User(), factories.User()])
    return group


@pytest.fixture
def open_group(factories):
    open_group = factories.OpenGroup()
    return open_group


@pytest.fixture
def no_creator_open_group(factories):
    open_group = factories.OpenGroup()
    open_group.creator = None
    return open_group


@pytest.fixture
def groups(group, open_group, no_creator_group, no_creator_open_group):
    return {"open_group": open_group,
            "group": group,
            "no_creator_open_group": no_creator_open_group,
            "no_creator_group": no_creator_group}


@pytest.fixture
def pyramid_request(pyramid_request):
    # Disconnect pyramid_request.POST from pyramid_request.params.
    # By default pyramid_request.POST and pyramid_request.params are the
    # same object so modifying one modifies the other. We actually want to
    # modify POST without modifying params in some of these tests so set them
    # to different objects.
    pyramid_request.POST = pyramid_request.params.copy()
    return pyramid_request


@pytest.fixture
def routes(pyramid_config):
    pyramid_config.add_route('activity.search', '/search')
    pyramid_config.add_route('activity.user_search', '/users/{username}')
    pyramid_config.add_route('group_read', '/groups/{pubid}/{slug}')
    pyramid_config.add_route('group_edit', '/groups/{pubid}/edit')
    pyramid_config.add_route('account_profile', '/account/profile')


@pytest.fixture
def annotation_stats_service(pyramid_config):
    pyramid_config.register_service(FakeAnnotationStatsService(), name='annotation_stats')


@pytest.fixture
def search(patch):
    search = patch('h.views.activity.SearchController.search')
    search.return_value = {
        'search_results': ActivityResults(total=200,
                                          aggregations={},
                                          timeframes=[]),
        'zero_message': 'No annotations matched your search.',
    }
    return search


@pytest.fixture
def user(factories):
    return factories.User()
