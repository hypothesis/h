# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import colander
import pytest
import mock

from h.models.group import (
    GROUP_NAME_MIN_LENGTH,
    GROUP_NAME_MAX_LENGTH,
    GROUP_DESCRIPTION_MAX_LENGTH,
)
from h.models.organization import Organization
from h.schemas.forms.admin.group import CreateAdminGroupSchema
from h.services.user import UserService


class TestCreateGroupSchema(object):
    def test_it_allows_with_valid_data(self, group_data, bound_schema):
        bound_schema.deserialize(group_data)

    def test_it_raises_if_name_too_short(self, group_data, bound_schema):
        too_short_name = "a" * (GROUP_NAME_MIN_LENGTH - 1)
        group_data["name"] = too_short_name

        with pytest.raises(colander.Invalid, match=".*name.*"):
            bound_schema.deserialize(group_data)

    def test_it_raises_if_name_too_long(self, group_data, bound_schema):
        too_long_name = "a" * (GROUP_NAME_MAX_LENGTH + 1)
        group_data["name"] = too_long_name

        with pytest.raises(colander.Invalid, match=".*name.*"):
            bound_schema.deserialize(group_data)

    def test_it_raises_if_description_too_long(self, group_data, bound_schema):
        too_long_description = "a" * (GROUP_DESCRIPTION_MAX_LENGTH + 1)
        group_data["description"] = too_long_description

        with pytest.raises(colander.Invalid, match=".*description.*"):
            bound_schema.deserialize(group_data)

    def test_it_raises_if_group_type_invalid(self, group_data, bound_schema):
        group_data["group_type"] = "foobarbazding"

        with pytest.raises(colander.Invalid, match=".*group_type.*"):
            bound_schema.deserialize(group_data)

    @pytest.mark.parametrize("required_field", ("name", "group_type", "creator"))
    def test_it_raises_if_required_field_missing(
        self, group_data, bound_schema, required_field
    ):
        group_data.pop(required_field)

        with pytest.raises(
            colander.Invalid, match=".*{field}.*".format(field=required_field)
        ):
            bound_schema.deserialize(group_data)

    @pytest.mark.parametrize("optional_field", ("description",))
    def test_it_allows_when_optional_field_missing(
        self, group_data, bound_schema, optional_field
    ):
        group_data.pop(optional_field)

        bound_schema.deserialize(group_data)

    @pytest.mark.parametrize(
        "invalid_scope", ["not-a-url", "foo:123", "example.com", "example.com/bar"]
    )
    def test_it_raises_if_origin_invalid(self, group_data, bound_schema, invalid_scope):
        group_data["scopes"] = [invalid_scope]
        with pytest.raises(colander.Invalid, match="scope.*must be a complete URL"):
            bound_schema.deserialize(group_data)

    def test_it_raises_if_no_origins(self, group_data, bound_schema):
        group_data["scopes"] = []
        with pytest.raises(colander.Invalid, match="At least one scope"):
            bound_schema.deserialize(group_data)

    def test_it_raises_if_group_type_changed(
        self, group_data, pyramid_csrf_request, org, user_svc
    ):
        group = mock.Mock(type="open")
        group_data["group_type"] = "restricted"
        schema = CreateAdminGroupSchema().bind(
            request=pyramid_csrf_request,
            group=group,
            user_svc=user_svc,
            organizations={org.pubid: org},
        )

        with pytest.raises(colander.Invalid, match="Changing group type"):
            schema.deserialize(group_data)

    def test_it_does_not_raise_if_group_type_is_same(
        self, group_data, pyramid_csrf_request, org, user_svc
    ):
        group = mock.Mock(type="open")
        group_data["group_type"] = "open"
        schema = CreateAdminGroupSchema().bind(
            request=pyramid_csrf_request,
            group=group,
            user_svc=user_svc,
            organizations={org.pubid: org},
        )

        schema.deserialize(group_data)

    def test_it_raises_if_member_invalid(self, group_data, bound_schema, user_svc):
        user_svc.fetch.return_value = None
        group_data["members"] = ["user_who_does_not_exist"]
        with pytest.raises(colander.Invalid, match="members.*Username not found"):
            bound_schema.deserialize(group_data)

    def test_it_allows_when_creator_exists_at_authority(self, group_data, bound_schema):
        bound_schema.deserialize(group_data)

    def test_it_passes_creator_and_authority_to_user_fetch(
        self, group_data, bound_schema, user_svc, org
    ):
        bound_schema.deserialize(group_data)
        user_svc.fetch.assert_called_with(group_data["creator"], org.authority)

    def test_it_allows_when_user_exists_at_authority(self, group_data, bound_schema):
        bound_schema.deserialize(group_data)

    def test_it_raises_when_the_creator_user_cannot_be_found(
        self, group_data, bound_schema, user_svc
    ):
        """
        It raises if there's no user with the given username and authority.

        It should raise if there's no user in the database with the same
        username as entered into the form and the same authority as the
        organization selected in the form.

        """
        user_svc.fetch.return_value = None
        with pytest.raises(
            colander.Invalid, match="^{'creator':.*'User not found.* at authority"
        ):
            bound_schema.deserialize(group_data)

    def test_it_lists_organizations(self, bound_schema, org):
        for child in bound_schema.children:
            if child.name == "organization":
                org_node = child
        assert org_node.widget.values == [
            (org.pubid, "{} ({})".format(org.name, org.authority))
        ]


@pytest.fixture
def group_data(factories):
    """
    Return a serialized representation of the "Create Group" form.

    This is the representation that Deform passes to Colander for
    deserialization and validation after the HTML form is processed by
    Peppercorn.
    """
    return {
        "name": "My Group",
        "group_type": "open",
        "creator": factories.User().username,
        "description": "Lorem ipsum dolor sit amet consectetuer",
        "organization": "__default__",
        "scopes": ["http://www.foo.com", "https://www.foo.com"],
        "enforce_scope": True,
    }


@pytest.fixture
def user_svc(pyramid_config):
    svc = mock.create_autospec(UserService, spec_set=True, instance=True)
    pyramid_config.register_service(svc, name="user")
    return svc


@pytest.fixture
def org(db_session):
    return Organization.default(db_session)


@pytest.fixture
def bound_schema(pyramid_csrf_request, org, user_svc):
    schema = CreateAdminGroupSchema().bind(
        request=pyramid_csrf_request, user_svc=user_svc, organizations={org.pubid: org}
    )
    return schema
