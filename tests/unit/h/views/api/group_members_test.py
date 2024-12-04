import logging
from unittest.mock import PropertyMock, call, create_autospec, sentinel

import pytest
from pyramid.httpexceptions import HTTPNoContent, HTTPNotFound

import h.views.api.group_members as views
from h import presenters
from h.models import GroupMembership
from h.schemas.base import ValidationError
from h.security.identity import Identity, LongLivedGroup, LongLivedMembership
from h.traversal import GroupContext, GroupMembershipContext
from h.views.api.exceptions import PayloadError


class TestListMembersLegacyLegacy:
    def test_it(
        self,
        context,
        pyramid_request,
        GroupMembershipJSONPresenter,
        group_members_service,
        caplog,
    ):
        pyramid_request.headers["User-Agent"] = sentinel.user_agent
        pyramid_request.headers["Referer"] = sentinel.referer
        group_members_service.get_memberships.return_value = [
            sentinel.membership_1,
            sentinel.membership_2,
        ]

        presenter_instances = GroupMembershipJSONPresenter.side_effect = [
            create_autospec(
                presenters.GroupMembershipJSONPresenter, instance=True, spec_set=True
            ),
            create_autospec(
                presenters.GroupMembershipJSONPresenter, instance=True, spec_set=True
            ),
        ]

        response = views.list_members_legacy(context, pyramid_request)

        assert caplog.messages == [
            f"list_members_legacy() was called. User-Agent: {sentinel.user_agent}, Referer: {sentinel.referer}, pubid: {context.group.pubid}"
        ]
        group_members_service.get_memberships.assert_called_once_with(context.group)
        assert GroupMembershipJSONPresenter.call_args_list == [
            call(pyramid_request, sentinel.membership_1),
            call(pyramid_request, sentinel.membership_2),
        ]
        presenter_instances[0].asdict.assert_called_once_with()
        presenter_instances[1].asdict.assert_called_once_with()
        assert response == [
            presenter_instances[0].asdict.return_value,
            presenter_instances[1].asdict.return_value,
        ]

    @pytest.fixture
    def context(self, factories):
        return create_autospec(
            GroupContext, instance=True, spec_set=True, group=factories.Group()
        )


class TestListMembers:
    def test_it(
        self,
        context,
        pyramid_request,
        GroupMembershipJSONPresenter,
        group_members_service,
        PaginationQueryParamsSchema,
        validate_query_params,
    ):
        pyramid_request.params = validate_query_params.return_value = {
            "page[offset]": 42,
            "page[limit]": 24,
        }
        group_members_service.count_memberships.return_value = 75
        group_members_service.get_memberships.return_value = [
            sentinel.membership_1,
            sentinel.membership_2,
        ]
        presenter_instances = GroupMembershipJSONPresenter.side_effect = [
            create_autospec(
                presenters.GroupMembershipJSONPresenter, instance=True, spec_set=True
            ),
            create_autospec(
                presenters.GroupMembershipJSONPresenter, instance=True, spec_set=True
            ),
        ]

        response = views.list_members(context, pyramid_request)

        PaginationQueryParamsSchema.assert_called_once_with()
        validate_query_params.assert_called_once_with(
            PaginationQueryParamsSchema.return_value, pyramid_request.params
        )
        group_members_service.count_memberships.assert_called_once_with(context.group)
        group_members_service.get_memberships.assert_called_once_with(
            context.group, offset=42, limit=24
        )
        assert GroupMembershipJSONPresenter.call_args_list == [
            call(pyramid_request, sentinel.membership_1),
            call(pyramid_request, sentinel.membership_2),
        ]
        presenter_instances[0].asdict.assert_called_once_with()
        presenter_instances[1].asdict.assert_called_once_with()
        assert response == {
            "meta": {
                "page": {"total": group_members_service.count_memberships.return_value}
            },
            "links": {
                "first": pyramid_request.route_url(
                    "api.group_members",
                    pubid=context.group.pubid,
                    _query={"page[offset]": 0, "page[limit]": 24},
                ),
                "last": pyramid_request.route_url(
                    "api.group_members",
                    pubid=context.group.pubid,
                    _query={"page[offset]": 72, "page[limit]": 24},
                ),
                "next": pyramid_request.route_url(
                    "api.group_members",
                    pubid=context.group.pubid,
                    _query={"page[offset]": 66, "page[limit]": 24},
                ),
                "prev": pyramid_request.route_url(
                    "api.group_members",
                    pubid=context.group.pubid,
                    _query={"page[offset]": 18, "page[limit]": 24},
                ),
            },
            "data": [
                presenter_instances[0].asdict.return_value,
                presenter_instances[1].asdict.return_value,
            ],
        }

    @pytest.mark.parametrize(
        "num_members,offset,limit,expected_links",
        [
            # We're on the first page, so there's no previous page.
            (100, 0, 10, {"first": 0, "last": 90, "next": 10, "prev": None}),
            # We're on a middle page, so there are both next and previous pages.
            (100, 40, 10, {"first": 0, "last": 90, "next": 50, "prev": 30}),
            # We're on the last page, so there's no next page.
            (100, 90, 10, {"first": 0, "last": 90, "next": None, "prev": 80}),
            # Things get weird of the given offset isn't a multiple of the given limit.
            (100, 2, 10, {"first": 0, "last": 90, "next": 12, "prev": 0}),
            (100, 12, 10, {"first": 0, "last": 90, "next": 22, "prev": 2}),
            (100, 92, 10, {"first": 0, "last": 90, "next": None, "prev": 82}),
        ],
    )
    def test_links(
        self,
        context,
        pyramid_request,
        group_members_service,
        validate_query_params,
        num_members,
        offset,
        limit,
        expected_links,
    ):
        group_members_service.count_memberships.return_value = num_members
        validate_query_params.return_value = {
            "page[offset]": offset,
            "page[limit]": limit,
        }

        response = views.list_members(context, pyramid_request)

        for link, expected_offset in expected_links.items():
            if expected_offset is None:
                assert response["links"][link] is None
            else:
                assert response["links"][link] == pyramid_request.route_url(
                    "api.group_members",
                    pubid=context.group.pubid,
                    _query={"page[offset]": expected_offset, "page[limit]": limit},
                )

    @pytest.fixture
    def context(self, factories):
        return create_autospec(
            GroupContext, instance=True, spec_set=True, group=factories.Group()
        )

    @pytest.fixture(autouse=True)
    def routes(self, pyramid_config):
        pyramid_config.add_route("api.group_members", "/api/groups/{pubid}/members")


class TestRemoveMember:
    def test_it(self, context, pyramid_request, group_members_service):
        response = views.remove_member(context, pyramid_request)

        group_members_service.member_leave.assert_called_once_with(
            context.group, context.user.userid
        )
        assert isinstance(response, HTTPNoContent)

    @pytest.fixture
    def context(self, factories):
        group = factories.Group.build()
        user = factories.User.build()
        membership = GroupMembership(group=group, user=user)
        return GroupMembershipContext(group=group, user=user, membership=membership)


@pytest.mark.usefixtures("group_members_service")
class TestAddMember:
    def test_it(self, pyramid_request, group_members_service, context):
        response = views.add_member(context, pyramid_request)

        group_members_service.member_join.assert_called_once_with(
            context.group, context.user.userid
        )
        assert isinstance(response, HTTPNoContent)

    def test_it_with_authority_mismatch(self, pyramid_request, context):
        context.group.authority = "other"

        with pytest.raises(HTTPNotFound):
            views.add_member(context, pyramid_request)

    @pytest.fixture
    def context(self, factories):
        group = factories.Group.build()
        user = factories.User.build(authority=group.authority)
        return GroupMembershipContext(group=group, user=user, membership=None)


class TestEditMember:
    def test_it(
        self,
        context,
        pyramid_request,
        EditGroupMembershipAPISchema,
        GroupMembershipJSONPresenter,
        caplog,
    ):
        response = views.edit_member(context, pyramid_request)

        EditGroupMembershipAPISchema.return_value.validate.assert_called_once_with(
            sentinel.json_body
        )
        assert context.membership.roles == sentinel.new_roles
        GroupMembershipJSONPresenter.assert_called_once_with(
            pyramid_request, context.membership
        )
        assert response == GroupMembershipJSONPresenter.return_value.asdict.return_value
        assert caplog.messages == [
            f"Changed group membership roles: {context.membership!r} (previous roles were: {sentinel.old_roles!r})",
        ]

    def test_noop(self, context, pyramid_request, EditGroupMembershipAPISchema, caplog):
        EditGroupMembershipAPISchema.return_value.validate.return_value["roles"] = (
            sentinel.old_roles
        )

        views.edit_member(context, pyramid_request)

        assert not caplog.messages

    def test_user_changing_own_role(self, context, pyramid_request, pyramid_config):
        context.user = pyramid_request.user
        identity = create_autospec(Identity, instance=True, spec_set=True)
        identity.user.memberships = [
            create_autospec(
                LongLivedMembership,
                instance=True,
                group=create_autospec(LongLivedGroup, instance=True, id="other"),
            ),
            create_autospec(
                LongLivedMembership,
                instance=True,
                group=create_autospec(
                    LongLivedGroup, instance=True, id=context.group.id
                ),
            ),
        ]
        pyramid_config.testing_securitypolicy(permissive=True, identity=identity)

        views.edit_member(context, pyramid_request)

        assert identity.user.memberships[1].roles == sentinel.new_roles

    def test_it_errors_if_the_user_doesnt_have_permission(
        self, context, pyramid_request, pyramid_config
    ):
        pyramid_config.testing_securitypolicy(permissive=False)

        with pytest.raises(HTTPNotFound):
            views.edit_member(context, pyramid_request)

    def test_it_errors_if_the_request_isnt_valid_JSON(
        self, context, pyramid_request, mocker
    ):
        value_error = ValueError()
        mocker.patch.object(
            type(pyramid_request),
            "json_body",
            PropertyMock(side_effect=value_error),
            create=True,
        )

        with pytest.raises(PayloadError) as exc_info:
            views.edit_member(context, pyramid_request)

        assert exc_info.value.__cause__ == value_error

    def test_it_errors_if_the_request_is_invalid(
        self, context, pyramid_request, EditGroupMembershipAPISchema
    ):
        EditGroupMembershipAPISchema.return_value.validate.side_effect = ValidationError

        with pytest.raises(ValidationError):
            views.edit_member(context, pyramid_request)

    @pytest.fixture
    def context(self, factories):
        group = factories.Group.build()
        user = factories.User.build(authority=group.authority)
        membership = GroupMembership(group=group, user=user, roles=sentinel.old_roles)

        return GroupMembershipContext(group=group, user=user, membership=membership)

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.json_body = sentinel.json_body
        return pyramid_request

    @pytest.fixture
    def EditGroupMembershipAPISchema(self, EditGroupMembershipAPISchema):
        EditGroupMembershipAPISchema.return_value.validate.return_value = {
            "roles": sentinel.new_roles
        }
        return EditGroupMembershipAPISchema

    @pytest.fixture(autouse=True)
    def pyramid_config(self, pyramid_config):
        pyramid_config.testing_securitypolicy(permissive=True)
        return pyramid_config


@pytest.fixture
def caplog(caplog):
    caplog.set_level(logging.INFO)
    return caplog


@pytest.fixture(autouse=True)
def EditGroupMembershipAPISchema(mocker):
    return mocker.patch(
        "h.views.api.group_members.EditGroupMembershipAPISchema",
        autospec=True,
        spec_set=True,
    )


@pytest.fixture(autouse=True)
def PaginationQueryParamsSchema(mocker):
    return mocker.patch(
        "h.views.api.group_members.PaginationQueryParamsSchema",
        autospec=True,
        spec_set=True,
    )


@pytest.fixture(autouse=True)
def validate_query_params(mocker):
    return mocker.patch(
        "h.views.api.group_members.validate_query_params", autospec=True, spec_set=True
    )


@pytest.fixture(autouse=True)
def GroupMembershipJSONPresenter(mocker):
    return mocker.patch(
        "h.views.api.group_members.GroupMembershipJSONPresenter",
        autospec=True,
        spec_set=True,
    )
