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


class TestGroupAPISchema:
    def test_it_sets_authority_properties(self, third_party_schema):
        assert third_party_schema.group_authority == "thirdparty.com"
        assert third_party_schema.default_authority == "hypothes.is"

    def test_it_ignores_non_whitelisted_properties(self, schema):
        appstruct = schema.validate(
            {
                "name": "A proper name",
                "organization": "foobar",
                "joinable_by": "whoever",
            }
        )

        assert "name" in appstruct
        assert "organization" not in appstruct
        assert "joinable_by" not in appstruct

    def test_it_raises_if_name_too_short(self, schema):
        with pytest.raises(ValidationError, match="name:.*is too short"):
            schema.validate({"name": "o" * (GROUP_NAME_MIN_LENGTH - 1)})

    def test_it_raises_if_name_too_long(self, schema):
        with pytest.raises(ValidationError, match="name:.*is too long"):
            schema.validate({"name": "o" * (GROUP_NAME_MAX_LENGTH + 1)})

    def test_it_validates_with_valid_name(self, schema):
        appstruct = schema.validate({"name": "Perfectly Fine"})

        assert "name" in appstruct

    def test_it_validates_with_valid_description(self, schema):
        appstruct = schema.validate(
            {
                "name": "This Seems Fine",
                "description": "This description seems adequate",
            }
        )

        assert "description" in appstruct

    def test_it_raises_if_description_too_long(self, schema):
        with pytest.raises(ValidationError, match="description:.*is too long"):
            schema.validate(
                {
                    "name": "Name not the Problem",
                    "description": "o" * (GROUP_DESCRIPTION_MAX_LENGTH + 1),
                }
            )

    def test_it_validates_with_valid_groupid_and_third_party_authority(
        self, third_party_schema
    ):
        appstruct = third_party_schema.validate(
            {"name": "This Seems Fine", "groupid": "group:1234abcd!~*()@thirdparty.com"}
        )

        assert "groupid" in appstruct

    def test_it_raises_if_groupid_too_long(self, schema):
        # Because of the complexity of ``groupid`` formatting, the length of the
        # ``authority_provided_id`` segment of it is defined in the pattern for
        # valid ``groupid``s — not as a length constraint
        # Note also that the groupid does not have a valid authority but validation
        # will raise on the formatting error before that becomes a problem.
        with pytest.raises(ValidationError, match="groupid:.*does not match"):
            schema.validate(
                {
                    "name": "Name not the Problem",
                    "groupid": "group:"
                    + ("o" * (AUTHORITY_PROVIDED_ID_MAX_LENGTH + 1))
                    + "@foobar.com",
                }
            )

    def test_it_raises_if_groupid_has_invalid_chars(self, schema):
        with pytest.raises(ValidationError, match="groupid:.*does not match"):
            schema.validate(
                {"name": "Name not the Problem", "groupid": "group:&&?@thirdparty.com"}
            )

    def test_validate_raises_ValidationError_on_groupid_if_first_party(self, schema):
        with pytest.raises(
            ValidationError,
            match="groupid may only be set on groups oustide of the default authority",
        ):
            schema.validate(
                {"name": "Less Good", "groupid": "group:delicacy@hypothes.is"}
            )

    def test_validate_raises_ValidationError_if_no_group_authority(self):
        schema = CreateGroupAPISchema(default_authority="hypothes.is")
        with pytest.raises(
            ValidationError,
            match="groupid may only be set on groups oustide of the default authority",
        ):
            schema.validate(
                {"name": "Blustery", "groupid": "group:delicacy@hypothes.is"}
            )

    def test_validate_raises_ValidationError_groupid_authority_mismatch(
        self, third_party_schema
    ):
        with pytest.raises(ValidationError, match="Invalid authority.*in groupid"):
            third_party_schema.validate(
                {"name": "Shambles", "groupid": "group:valid_id@invalidauthority.com"}
            )

    @pytest.fixture
    def schema(self):
        schema = GroupAPISchema(
            group_authority="hypothes.is", default_authority="hypothes.is"
        )
        return schema

    @pytest.fixture
    def third_party_schema(self):
        schema = GroupAPISchema(
            group_authority="thirdparty.com", default_authority="hypothes.is"
        )
        return schema


class TestCreateGroupAPISchema:
    def test_it_raises_if_name_missing(self, schema):
        with pytest.raises(ValidationError, match=".*is a required property.*"):
            schema.validate({})

    @pytest.fixture
    def schema(self):
        schema = CreateGroupAPISchema(
            group_authority="hypothes.is", default_authority="hypothes.is"
        )
        return schema


class TestUpdateGroupAPISchema:
    def test_it_allows_empty_payload(self, schema):
        appstruct = schema.validate({})

        assert appstruct == {}

    @pytest.fixture
    def schema(self):
        schema = UpdateGroupAPISchema(
            group_authority="hypothes.is", default_authority="hypothes.is"
        )
        return schema
