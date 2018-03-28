# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime

from pyramid.httpexceptions import HTTPNotFound
import pytest
import mock

from h.models import User
from h.views import admin_groups
from h.views.admin_groups import GroupCreateController, GroupEditController
from h.services.user import UserService
from h.services.group import GroupService
from h.services.delete_group import DeleteGroupService


class FakeForm(object):
    def set_appstruct(self, appstruct):
        self.appstruct = appstruct

    def render(self):
        return self.appstruct


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


@pytest.mark.parametrize('query,expected_groups', [
    # All groups should be returned when there is no query.
    (None, ['BioPub', 'ChemPub', 'Public']),

    # Only matching groups should be returned if there is a query.
    ('BioPub', ['BioPub']),
    ('ChemPub', ['ChemPub']),

    # Filtering should be case-insensitive.
    ('chem', ['ChemPub']),
])
def test_index_filters_results(pyramid_request, factories, query, expected_groups):
    factories.Group(name='BioPub')
    factories.Group(name='ChemPub')

    if query:
        pyramid_request.GET['q'] = query
    ctx = admin_groups.groups_index(None, pyramid_request)

    filtered_group_names = sorted([g.name for g in ctx['results']])
    assert filtered_group_names == expected_groups


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
        expected_userid = User(username=creator, authority=pyramid_request.authority).userid

        create_method.assert_called_with(name=name, userid=expected_userid, description=description,
                                         origins=origins)


@pytest.mark.usefixtures('routes', 'user_svc')
class TestGroupEditController(object):

    def test_it_binds_schema(self, pyramid_request, group, patch):
        schema = mock.Mock(spec_set=['bind'])
        CreateAdminGroupSchema = patch('h.views.admin_groups.CreateAdminGroupSchema')  # noqa: N806
        CreateAdminGroupSchema.return_value = schema
        pyramid_request.matchdict = {'pubid': group.pubid}

        GroupEditController(pyramid_request)

        schema.bind.assert_called_with(request=pyramid_request, group=group)

    def test_raises_not_found_if_unknown_group(self, pyramid_request):
        pyramid_request.matchdict = {'pubid': 'unknown'}
        with pytest.raises(HTTPNotFound):
            GroupEditController(pyramid_request)

    def test_read_renders_form(self, pyramid_request, factories, group):
        pyramid_request.matchdict = {'pubid': group.pubid}
        factories.Annotation(groupid=group.pubid)
        factories.Annotation(groupid=group.pubid)

        ctrl = GroupEditController(pyramid_request)

        ctx = ctrl.read()

        assert ctx['form'] == self._expected_form(group)
        assert ctx['pubid'] == group.pubid
        assert ctx['group_name'] == group.name
        assert ctx['member_count'] == len(group.members)
        assert ctx['annotation_count'] == 2

    def test_read_renders_form_if_group_has_no_creator(self, pyramid_request, group):
        pyramid_request.matchdict = {'pubid': group.pubid}
        group.creator = None
        ctrl = GroupEditController(pyramid_request)

        ctx = ctrl.read()

        assert ctx['form'] == self._expected_form(group)

    def test_update_updates_group_on_success(self, factories, pyramid_request, group, group_svc, user_svc, handle_form_submission):
        pyramid_request.matchdict = {'pubid': group.pubid}

        updated_name = 'Updated group'
        updated_creator = factories.User()
        user_svc.fetch.return_value = updated_creator
        updated_description = 'New description'
        updated_origins = ['https://a-new-site.com']

        def call_on_success(request, form, on_success, on_failure):
            return on_success({
                'authority': pyramid_request.authority,
                'creator': updated_creator.username,
                'description': updated_description,
                'group_type': 'open',
                'name': updated_name,
                'origins': updated_origins,
            })
        handle_form_submission.side_effect = call_on_success
        ctrl = GroupEditController(pyramid_request)

        ctx = ctrl.update()

        assert group.creator.username == updated_creator.username
        assert group.description == updated_description
        assert group.name == updated_name
        assert [s.origin for s in group.scopes] == updated_origins
        assert ctx['form'] == self._expected_form(group)

    def test_update_does_not_update_authority(self, pyramid_request, group, user_svc, handle_form_submission):
        pyramid_request.matchdict = {'pubid': group.pubid}
        user_svc.fetch.return_value = group.creator
        group.authority = 'original.com'

        def call_on_success(request, form, on_success, on_failure):
            return on_success({
                'authority': 'different.com',
                'creator': group.creator.username,
                'description': group.description,
                'group_type': 'open',
                'name': group.name,
                'origins': [s.origin for s in group.scopes],
            })
        handle_form_submission.side_effect = call_on_success
        ctrl = GroupEditController(pyramid_request)

        ctx = ctrl.update()

        assert group.authority == 'original.com'
        assert ctx['form'] == self._expected_form(group)

    def test_delete_deletes_group(self, group, delete_group_svc, pyramid_request, routes):
        pyramid_request.matchdict = {"pubid": group.pubid}

        ctrl = GroupEditController(pyramid_request)

        ctrl.delete()

        delete_group_svc.delete.assert_called_once_with(group)

    @pytest.fixture
    def group(self, factories):
        return factories.OpenGroup(pubid='testgroup')

    def _expected_form(self, group):
        return {'authority': group.authority,
                'creator': group.creator.username if group.creator else '',
                'description': group.description or '',
                'group_type': group.type,
                'name': group.name,
                'origins': [s.origin for s in group.scopes]}


@pytest.fixture
def authority():
    return 'foo.com'


@pytest.fixture
def pyramid_request(pyramid_request, factories, authority):
    pyramid_request.session = mock.Mock(spec_set=['flash', 'get_csrf_token'])
    pyramid_request.user = factories.User(authority=authority)
    pyramid_request.create_form.return_value = FakeForm()
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


@pytest.fixture
def delete_group_svc(pyramid_config, pyramid_request):
    service = mock.Mock(spec_set=DeleteGroupService(request=pyramid_request))
    pyramid_config.register_service(service, name='delete_group')
    return service
