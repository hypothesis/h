import pytest

from h.models.group import (
    AUTHORITY_PROVIDED_ID_MAX_LENGTH,
    GROUP_DESCRIPTION_MAX_LENGTH,
    GROUP_NAME_MAX_LENGTH,
    GROUP_NAME_MIN_LENGTH,
)
from h.schemas import ValidationError
from h.schemas.api.group import (
    CreateGroupAPISchema,
    GroupAPISchema,
    UpdateGroupAPISchema,
)

DEFAULT_AUTHORITY = "hypothes.is"


class TestGroupAPISchema:
    @pytest.mark.parametrize(
        "group_authority,data,expected_appstruct",
        [
            (  # An empty dict is valid input data.
                DEFAULT_AUTHORITY,
                {},
                {},
            ),
            (  # Valid group name.
                DEFAULT_AUTHORITY,
                {"name": "Valid Group Name"},
                {"name": "Valid Group Name"},
            ),
            (  # Valid group description.
                DEFAULT_AUTHORITY,
                {"description": "Valid group description."},
                {"description": "Valid group description."},
            ),
            (  # Valid groupid (requires matching third-party authority).
                "thirdparty.com",
                {"groupid": "group:1234abcd!~*()@thirdparty.com"},
                {"groupid": "group:1234abcd!~*()@thirdparty.com"},
            ),
            (  # Valid type.
                DEFAULT_AUTHORITY,
                {"type": "private"},
                {"type": "private"},
            ),
            (  # Valid type.
                DEFAULT_AUTHORITY,
                {"type": "restricted"},
                {"type": "restricted"},
            ),
            (  # Valid type.
                DEFAULT_AUTHORITY,
                {"type": "open"},
                {"type": "open"},
            ),
            (  # All valid fields at once.
                "thirdparty.com",
                {
                    "name": "Valid Group Name",
                    "description": "Valid group description.",
                    "groupid": "group:1234abcd!~*()@thirdparty.com",
                },
                {
                    "name": "Valid Group Name",
                    "description": "Valid group description.",
                    "groupid": "group:1234abcd!~*()@thirdparty.com",
                },
            ),
            (  # It ignores non-whitelisted properties.
                DEFAULT_AUTHORITY,
                {
                    "organization": "foobar",
                    "joinable_by": "whoever",
                },
                {},
            ),
        ],
    )
    def test_valid(self, group_authority, data, expected_appstruct):
        schema = GroupAPISchema(
            group_authority=group_authority, default_authority=DEFAULT_AUTHORITY
        )

        assert schema.validate(data) == expected_appstruct

    @pytest.mark.parametrize(
        "group_authority,data,error_message",
        [
            (
                # Name too short.
                DEFAULT_AUTHORITY,
                {"name": "o" * (GROUP_NAME_MIN_LENGTH - 1)},
                "name:.*is too short",
            ),
            (
                # Name too long.
                DEFAULT_AUTHORITY,
                {"name": "o" * (GROUP_NAME_MAX_LENGTH + 1)},
                "name:.*is too long",
            ),
            (
                # Name isn't a string.
                DEFAULT_AUTHORITY,
                {"name": 42},
                "name: 42 is not of type 'string'",
            ),
            (
                # Name has leading whitespace.
                DEFAULT_AUTHORITY,
                {"name": f" {'o' * GROUP_NAME_MIN_LENGTH}"},
                "Group names can't have leading or trailing whitespace.",
            ),
            (
                # Name has trailing whitespace.
                DEFAULT_AUTHORITY,
                {"name": f"{'o' * GROUP_NAME_MIN_LENGTH} "},
                "Group names can't have leading or trailing whitespace.",
            ),
            (
                # Whitespace-only name.
                DEFAULT_AUTHORITY,
                {"name": " " * GROUP_NAME_MIN_LENGTH},
                "Group names can't have leading or trailing whitespace.",
            ),
            (
                # Description too long.
                DEFAULT_AUTHORITY,
                {"description": "o" * (GROUP_DESCRIPTION_MAX_LENGTH + 1)},
                "description:.*is too long",
            ),
            (
                # groupid too long.
                "thirdparty.com",
                {
                    "groupid": f"group:{'o' * (AUTHORITY_PROVIDED_ID_MAX_LENGTH + 1)}@thirdparty.com",
                },
                "groupid:.*does not match",
            ),
            (
                # groupid has invalid chars.
                "thirdparty.com",
                {"groupid": "group:&&?@thirdparty.com"},
                "groupid:.*does not match",
            ),
            (
                # Custom groupid's aren't allowed for first-party groups.
                DEFAULT_AUTHORITY,
                {"groupid": f"group:delicacy@{DEFAULT_AUTHORITY}"},
                "groupid may only be set on groups outside of the default authority",
            ),
            (
                # groupid authority mismatch.
                "thirdparty.com",
                {"groupid": "group:delicacy@invalidauthority.com"},
                "Invalid authority.*in groupid",
            ),
            (
                # groupid not a string.
                "thirdparty.com",
                {"groupid": 42},
                "groupid: 42 is not of type 'string'",
            ),
            (
                # type not a string.
                DEFAULT_AUTHORITY,
                {"type": 42},
                r"type: 42 is not one of \['private', 'restricted', 'open'\]",
            ),
            (
                # Invalid type.
                DEFAULT_AUTHORITY,
                {"type": "invalid"},
                r"type: 'invalid' is not one of \['private', 'restricted', 'open'\]",
            ),
        ],
    )
    def test_invalid(self, group_authority, data, error_message):
        schema = GroupAPISchema(
            group_authority=group_authority, default_authority=DEFAULT_AUTHORITY
        )

        with pytest.raises(ValidationError, match=error_message):
            schema.validate(data)

    def test_it_sets_authority_properties(self):
        schema = GroupAPISchema(
            group_authority="thirdparty.com", default_authority=DEFAULT_AUTHORITY
        )

        assert schema.group_authority == "thirdparty.com"
        assert schema.default_authority == DEFAULT_AUTHORITY


class TestCreateGroupAPISchema:
    def test_it_raises_if_name_missing(self, schema):
        with pytest.raises(ValidationError, match="'name' is a required property.*"):
            schema.validate({})

    @pytest.fixture
    def schema(self):
        schema = CreateGroupAPISchema(
            group_authority=DEFAULT_AUTHORITY, default_authority=DEFAULT_AUTHORITY
        )
        return schema


class TestUpdateGroupAPISchema:
    def test_it_allows_empty_payload(self, schema):
        appstruct = schema.validate({})

        assert appstruct == {}

    @pytest.fixture
    def schema(self):
        schema = UpdateGroupAPISchema(
            group_authority=DEFAULT_AUTHORITY, default_authority=DEFAULT_AUTHORITY
        )
        return schema
