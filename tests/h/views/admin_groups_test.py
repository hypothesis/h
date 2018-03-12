# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime

import pytest
import mock

# from h.models.auth_client import AuthClient, GrantType, ResponseType
from h.views import admin_groups
from h.views.admin_groups import GroupCreateController
from h.services.user import UserService
from h.services.group import GroupService


def test_index_lists_groups_sorted_by_created_desc(pyramid_request, routes, factories, authority):
    groups = [factories.Group(created=datetime.datetime(2017, 8, 2)),
              factories.Group(created=datetime.datetime(2015, 2, 1)),
              factories.Group(),
              factories.Group(created=datetime.datetime(2013, 2, 1))]

    ctx = admin_groups.groups_index(None, pyramid_request)

    # We can't avoid getting the Public group back, which is created outside of
    # these tests' sphere of influence. Remove it as it is not feasible to
    # assert where it will appear in creation order.
    filtered_groups = list(filter(lambda group: group.pubid != '__world__',
                                  ctx['results']))

    expected_groups = [groups[2], groups[0], groups[1], groups[3]]
    assert filtered_groups == expected_groups


def test_index_paginates_results(pyramid_request, routes, paginate):
    admin_groups.groups_index(None, pyramid_request)

    paginate.assert_called_once_with(pyramid_request, mock.ANY, mock.ANY)


@pytest.mark.usefixtures('group_svc', 'routes', 'user_svc')
class TestGroupCreateController(object):

    def test_get_sets_form(self, pyramid_request):
        ctrl = GroupCreateController(pyramid_request)

        ctx = ctrl.get()

        assert 'form' in ctx

    def test_it_handles_form_submission(self, pyramid_request, handle_form_submission, matchers):
        ctrl = GroupCreateController(pyramid_request)

        ctrl.post()

        handle_form_submission.assert_called_once_with(
            ctrl.request,
            ctrl.form,
            matchers.any_callable(),
            ctrl._template_context
        )

    def test_post_redirects_to_list_view_on_success(self, pyramid_request, matchers, routes, handle_form_submission):
        def call_on_success(request, form, on_success, on_failure):
            return on_success({
                'name': 'My New Group',
                'group_type': 'restricted',
                'creator': pyramid_request.user.username,
                'description': None,
                'authority': pyramid_request.authority,
                'origins': []
            })
        handle_form_submission.side_effect = call_on_success
        ctrl = GroupCreateController(pyramid_request)

        response = ctrl.post()

        expected_location = pyramid_request.route_url('admin_groups')
        assert response == matchers.redirect_302_to(expected_location)

    @pytest.mark.parametrize('type_', [
        'open',
        'restricted',
    ])
    def test_post_creates_group_on_success(self, pyramid_request, group_svc, handle_form_submission, type_):
        name = 'My new group'
        creator = pyramid_request.user.username
        description = 'Purpose of new group'
        origins = ['https://example.com']

        def call_on_success(request, form, on_success, on_failure):
            return on_success({
                'authority': pyramid_request.authority,
                'creator': creator,
                'description': description,
                'group_type': type_,
                'name': name,
                'origins': origins,
            })
        handle_form_submission.side_effect = call_on_success
        ctrl = GroupCreateController(pyramid_request)

        ctrl.post()

        if type_ == 'open':
            create_method = group_svc.create_open_group
        else:
            create_method = group_svc.create_restricted_group
        expected_userid = 'acct:{}@{}'.format(creator, pyramid_request.authority)

        create_method.assert_called_with(name=name, userid=expected_userid, description=description,
                                         origins=origins)


@pytest.fixture
def authority():
    return 'foo.com'


@pytest.fixture
def pyramid_request(pyramid_request, factories, authority):
    pyramid_request.session = mock.Mock(spec_set=['flash', 'get_csrf_token'])
    pyramid_request.user = factories.User(authority=authority)
    return pyramid_request


@pytest.fixture
def paginate(patch):
    return patch('h.views.admin_groups.paginator.paginate')


@pytest.fixture
def handle_form_submission(patch):
    return patch('h.views.admin_groups.form.handle_form_submission')


@pytest.fixture
def routes(pyramid_config):
    pyramid_config.add_route('admin_groups', '/admin/groups')
    pyramid_config.add_route('admin_groups_create', '/admin/groups/new')
    pyramid_config.add_route('group_read', '/groups/{pubid}/{slug}')


@pytest.fixture
def user_svc(pyramid_config):
    svc = mock.create_autospec(UserService, spec_set=True, instance=True)
    pyramid_config.register_service(svc, name='user')
    return svc


@pytest.fixture
def group_svc(pyramid_config):
    svc = mock.create_autospec(GroupService, spec_set=True, instance=True)
    pyramid_config.register_service(svc, name='group')
    return svc
