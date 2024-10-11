from unittest import mock
from unittest.mock import call

import colander
import pytest

from h.models.group import (
    GROUP_DESCRIPTION_MAX_LENGTH,
    GROUP_NAME_MAX_LENGTH,
    GROUP_NAME_MIN_LENGTH,
)
from h.models.organization import Organization
from h.schemas.forms.admin.group import AdminGroupSchema


class TestAdminGroupSchema:
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

        with pytest.raises(colander.Invalid, match=f".*{required_field}.*"):
            bound_schema.deserialize(group_data)

    @pytest.mark.parametrize("optional_field", ("description", "organization"))
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

    def test_it_allows_no_scopes(self, group_data, bound_schema):
        group_data["scopes"] = []

        bound_schema.deserialize(group_data)

    def test_it_raises_if_group_type_changed(
        self, group_data, pyramid_csrf_request, org, user_service
    ):
        group = mock.Mock(type="open")
        group_data["group_type"] = "restricted"
        schema = AdminGroupSchema().bind(
            request=pyramid_csrf_request,
            group=group,
            user_svc=user_service,
            organizations={org.pubid: org},
        )

        with pytest.raises(colander.Invalid, match="Changing group type"):
            schema.deserialize(group_data)

    def test_it_does_not_raise_if_group_type_is_same(
        self, group_data, pyramid_csrf_request, org, user_service
    ):
        group = mock.Mock(type="open")
        group_data["group_type"] = "open"
        schema = AdminGroupSchema().bind(
            request=pyramid_csrf_request,
            group=group,
            user_svc=user_service,
            organizations={org.pubid: org},
        )

        schema.deserialize(group_data)

    def test_it_raises_if_member_invalid(self, group_data, bound_schema, user_service):
        user_service.fetch.return_value = None

        group_data["members"] = ["valid_user", "invalid_user"]
        with pytest.raises(colander.Invalid, match="members.1"):
            bound_schema.deserialize(group_data)

    def test_it_passes_through_the_authority_when_checking_users(
        self, group_data, bound_schema, user_service, third_party_org
    ):
        group_data["organization"] = third_party_org.pubid
        group_data["members"] = ["valid_user"]
        group_data["creator"] = "valid_creator"

        bound_schema.deserialize(group_data)

        user_service.fetch.assert_has_calls(
            (
                # It's a bit of a shame to enshrine the order, as it really
                # doesn't matter, but it's the easiest thing to do
                call("valid_user", third_party_org.authority),
                call("valid_creator", third_party_org.authority),
            )
        )

    def test_it_allows_when_creator_exists_at_authority(self, group_data, bound_schema):
        bound_schema.deserialize(group_data)

    def test_it_passes_creator_and_authority_to_user_fetch(
        self, group_data, bound_schema, user_service, org
    ):
        bound_schema.deserialize(group_data)
        user_service.fetch.assert_called_with(group_data["creator"], org.authority)

    def test_it_allows_when_user_exists_at_authority(self, group_data, bound_schema):
        bound_schema.deserialize(group_data)

    def test_it_raises_when_the_creator_user_cannot_be_found(
        self, group_data, bound_schema
    ):
        """
        It raises if there's no user with the given username and authority.

        It should raise if there's no user in the database with the same
        username as entered into the form and the same authority as the
        organization selected in the form.

        """
        group_data["creator"] = "invalid_creator"
        with pytest.raises(colander.Invalid, match="creator"):
            bound_schema.deserialize(group_data)

    def test_it_lists_organizations(self, bound_schema, org, third_party_org):
        for child in bound_schema.children:
            if child.name == "organization":
                org_node = child

        # pylint:disable=possibly-used-before-assignment
        assert org_node.widget.values == [
            ("", "-- None --"),
            (org.pubid, f"{org.name} ({org.authority})"),
            (
                third_party_org.pubid,
                f"{third_party_org.name} ({third_party_org.authority})",
            ),
        ]


@pytest.fixture
def group_data(org):
    """
    Return a serialized representation of the "Create Group" form.

    This is the representation that Deform passes to Colander for
    deserialization and validation after the HTML form is processed by
    Peppercorn.
    """
    return {
        "name": "My Group",
        "group_type": "open",
        "creator": "valid_creator",
        "description": "Lorem ipsum dolor sit amet consectetuer",
        "organization": org.pubid,
        "scopes": ["http://www.foo.com", "https://www.foo.com"],
        "enforce_scope": True,
    }


@pytest.fixture
def user_service(user_service, factories):
    def fetch(username, authority):  # pylint: disable=unused-argument
        if "invalid" in username:
            return False

        return factories.User()

    user_service.fetch.side_effect = fetch

    return user_service


@pytest.fixture
def org(factories):
    return factories.Organization()


@pytest.fixture
def third_party_org(db_session):
    third_party_org = Organization(
        name="3rd_party", pubid="3rd_party_id", authority="3rd_party_authority"
    )
    db_session.add(third_party_org)

    return third_party_org


@pytest.fixture
def bound_schema(pyramid_csrf_request, org, third_party_org, user_service):
    schema = AdminGroupSchema().bind(
        request=pyramid_csrf_request,
        user_svc=user_service,
        organizations={org.pubid: org, third_party_org.pubid: third_party_org},
    )
    return schema
