import pytest

from h.schemas import ValidationError
from h.schemas.api.group_membership import EditGroupMembershipAPISchema


class TestEditGroupMembershipAPISchema:
    @pytest.mark.parametrize(
        "data,expected_appstruct",
        [
            ({"roles": ["member"]}, {"roles": ["member"]}),
            ({"roles": ["moderator"]}, {"roles": ["moderator"]}),
            ({"roles": ["admin"]}, {"roles": ["admin"]}),
            ({"roles": ["owner"]}, {"roles": ["owner"]}),
        ],
    )
    def test_valid(self, schema, data, expected_appstruct):
        assert schema.validate(data) == expected_appstruct

    @pytest.mark.parametrize(
        "data,error_message",
        [
            ({"roles": ["unknown"]}, r"^roles\.0: 'unknown' is not one of \[[^]]*\]$"),
            ({"roles": []}, r"^roles: \[\] should be non-empty$"),
            ({"roles": ["member", "moderator"]}, r"^roles: \[[^]]*\] is too long$"),
            ({"roles": 42}, r"^roles: 42 is not of type 'array'$"),
            ({}, r"^'roles' is a required property$"),
        ],
    )
    def test_invalid(self, schema, data, error_message):
        with pytest.raises(ValidationError, match=error_message):
            schema.validate(data)

    @pytest.fixture
    def schema(self):
        return EditGroupMembershipAPISchema()
