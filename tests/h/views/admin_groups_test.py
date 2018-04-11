# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime

from pyramid.httpexceptions import HTTPNotFound
import pytest
import mock

from h.models import Organization, User
from h.views import admin_groups
from h.views.admin_groups import GroupCreateController, GroupEditController
from h.services.user import UserService
from h.services.group import GroupService
from h.services.delete_group import DeleteGroupService
from h.services.list_organizations import ListOrganizationsService


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


@pytest.mark.usefixtures('group_svc', 'list_orgs_svc', 'routes', 'user_svc')
class TestGroupCreateController(object):

    def test_get_sets_form(self, pyramid_request):
        ctrl = GroupCreateController(pyramid_request)

        ctx = ctrl.get()

        assert 'form' in ctx

    def test_get_lists_all_organizations(self, pyramid_request, factories, default_org,  # noqa: N803
                                         CreateAdminGroupSchema, list_orgs_svc):
        GroupCreateController(pyramid_request)

        list_orgs_svc.organizations.assert_called_with()
        schema = CreateAdminGroupSchema.return_value
        (_, call_kwargs) = schema.bind.call_args
        assert call_kwargs['organizations'] == list_orgs_svc.organizations.return_value

    def test_it_handles_form_submission(self, pyramid_request, handle_form_submission, matchers):
        ctrl = GroupCreateController(pyramid_request)

        ctrl.post()

        handle_form_submission.assert_called_once_with(
            ctrl.request,
            ctrl.form,
            matchers.any_callable(),
            ctrl._template_context
        )

    def test_post_redirects_to_list_view_on_success(self, pyramid_request,
                                                    matchers, routes, handle_form_submission, default_org):
        def call_on_success(request, form, on_success, on_failure):
            return on_success({
                'name': 'My New Group',
                'group_type': 'restricted',
                'creator': pyramid_request.user.username,
                'description': None,
                'members': [],
                'organization': default_org.pubid,
                'origins': [],
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
    def test_post_creates_group_on_success(self, factories, pyramid_request, group_svc, handle_form_submission,
                                           type_, default_org):
        name = 'My new group'
        creator = pyramid_request.user.username
        member_to_add = 'member_to_add'
        description = 'Purpose of new group'
        origins = ['https://example.com']

        def call_on_success(request, form, on_success, on_failure):
            return on_success({
                'organization': default_org.pubid,
                'creator': creator,
                'description': description,
                'group_type': type_,
                'name': name,
                'origins': origins,
                'members': [member_to_add]
            })
        handle_form_submission.side_effect = call_on_success
        ctrl = GroupCreateController(pyramid_request)

        if type_ == 'open':
            create_method = group_svc.create_open_group
        else:
            create_method = group_svc.create_restricted_group

        create_method.return_value = factories.RestrictedGroup(pubid='testgroup')
        ctrl.post()

        expected_userid = User(username=creator, authority=pyramid_request.authority).userid

        create_method.assert_called_with(name=name, userid=expected_userid, description=description,
                                         origins=origins, organization=default_org)
        group_svc.update_membership.assert_called_once_with(create_method.return_value, [member_to_add])


@pytest.mark.usefixtures('routes', 'user_svc', 'group_svc', 'list_orgs_svc')
class TestGroupEditController(object):

    def test_it_binds_schema(self, pyramid_request, group, user_svc,  # noqa: N803
                             default_org, CreateAdminGroupSchema):
        pyramid_request.matchdict = {'pubid': group.pubid}

        GroupEditController(pyramid_request)

        schema = CreateAdminGroupSchema.return_value
        schema.bind.assert_called_with(request=pyramid_request, group=group,
                                       user_svc=user_svc, organizations=[default_org])

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

    def test_read_lists_organizations_in_groups_authority(self, factories, pyramid_request, group,  # noqa: N803
                                                          default_org, CreateAdminGroupSchema,
                                                          list_orgs_svc):
        pyramid_request.matchdict = {'pubid': group.pubid}

        GroupEditController(pyramid_request)

        list_orgs_svc.organizations.assert_called_with(group.authority)
        schema = CreateAdminGroupSchema.return_value
        (_, call_kwargs) = schema.bind.call_args
        assert call_kwargs['organizations'] == list_orgs_svc.organizations.return_value

    def test_update_updates_group_on_success(self, factories, pyramid_request, group_svc, user_svc,
                                             handle_form_submission):
        group = factories.RestrictedGroup(pubid='testgroup')
        pyramid_request.matchdict = {'pubid': group.pubid}

        updated_name = 'Updated group'
        updated_creator = factories.User()
        user_svc.fetch.return_value = updated_creator
        updated_description = 'New description'
        updated_origins = ['https://a-new-site.com']
        updated_members = []
        updated_org = factories.Organization()

        def call_on_success(request, form, on_success, on_failure):
            return on_success({
                'creator': updated_creator.username,
                'description': updated_description,
                'group_type': 'open',
                'name': updated_name,
                'organization': updated_org.pubid,
                'origins': updated_origins,
                'members': updated_members,
            })
        handle_form_submission.side_effect = call_on_success
        ctrl = GroupEditController(pyramid_request)

        ctx = ctrl.update()

        assert group.creator.username == updated_creator.username
        assert group.description == updated_description
        assert group.name == updated_name
        assert group.organization == updated_org
        assert [s.origin for s in group.scopes] == updated_origins
        assert ctx['form'] == self._expected_form(group)

    def test_update_updates_group_membership_on_success(self, factories, pyramid_request, group_svc, user_svc, handle_form_submission):
        group = factories.RestrictedGroup(pubid='testgroup')

        pyramid_request.matchdict = {'pubid': group.pubid}

        member_a = factories.User()
        member_b = factories.User()

        updated_creator = factories.User()
        user_svc.fetch.return_value = updated_creator

        def call_on_success(request, form, on_success, on_failure):
            return on_success({
                'authority': pyramid_request.authority,
                'creator': updated_creator.username,
                'description': 'a desc',
                'group_type': 'restricted',
                'name': 'a name',
                'members': [member_a.username, member_b.username],
                'organization': group.organization.pubid,
                'origins': ['http://www.example.com'],
            })
        handle_form_submission.side_effect = call_on_success
        ctrl = GroupEditController(pyramid_request)

        ctrl.update()

        group_svc.update_membership.assert_any_call(group, [member_a.username, member_b.username])

    def test_delete_deletes_group(self, group, delete_group_svc, pyramid_request, routes):
        pyramid_request.matchdict = {"pubid": group.pubid}

        ctrl = GroupEditController(pyramid_request)

        ctrl.delete()

        delete_group_svc.delete.assert_called_once_with(group)

    @pytest.fixture
    def group(self, factories):
        return factories.OpenGroup(pubid='testgroup')

    def _expected_form(self, group):
        return {'creator': group.creator.username if group.creator else '',
                'description': group.description or '',
                'group_type': group.type,
                'name': group.name,
                'members': [m.username for m in group.members],
                'organization': group.organization.pubid,
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


@pytest.fixture
def list_orgs_svc(pyramid_config, db_session):
    svc = mock.Mock(spec_set=ListOrganizationsService(db_session))
    svc.organizations.return_value = [Organization.default(db_session)]
    pyramid_config.register_service(svc, name='list_organizations')
    return svc


@pytest.fixture
def CreateAdminGroupSchema(patch):  # noqa: N802
    schema = mock.Mock(spec_set=['bind'])
    CreateAdminGroupSchema = patch('h.views.admin_groups.CreateAdminGroupSchema')  # noqa: N806
    CreateAdminGroupSchema.return_value = schema
    return CreateAdminGroupSchema


@pytest.fixture
def default_org(db_session):
    return Organization.default(db_session)
