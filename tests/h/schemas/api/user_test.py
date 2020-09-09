import pytest

from h.schemas import ValidationError
from h.schemas.api.user import CreateUserAPISchema, UpdateUserAPISchema


class TestCreateUserAPISchema:
    def test_it_raises_when_authority_missing(self, schema, payload):
        del payload["authority"]

        with pytest.raises(ValidationError):
            schema.validate(payload)

    def test_it_raises_when_authority_not_a_string(self, schema, payload):
        payload["authority"] = 34

        with pytest.raises(ValidationError):
            schema.validate(payload)

    def test_it_raises_when_username_missing(self, schema, payload):
        del payload["username"]

        with pytest.raises(ValidationError):
            schema.validate(payload)

    def test_it_raises_when_username_not_a_string(self, schema, payload):
        payload["username"] = ["hello"]

        with pytest.raises(ValidationError):
            schema.validate(payload)

    def test_it_raises_when_username_empty(self, schema, payload):
        payload["username"] = ""

        with pytest.raises(ValidationError):
            schema.validate(payload)

    def test_it_raises_when_username_too_short(self, schema, payload):
        payload["username"] = "da"

        with pytest.raises(ValidationError):
            schema.validate(payload)

    def test_it_raises_when_username_too_long(self, schema, payload):
        payload["username"] = "dagrun-lets-make-this-username-really-long"

        with pytest.raises(ValidationError):
            schema.validate(payload)

    def test_it_raises_when_username_format_invalid(self, schema, payload):
        payload["username"] = "dagr!un"

        with pytest.raises(ValidationError):
            schema.validate(payload)

    def test_it_raises_when_email_and_identities_missing(self, schema, payload):
        del payload["email"]

        with pytest.raises(ValidationError):
            schema.validate(payload)

    def test_it_raises_when_email_empty_and_identities_missing(self, schema, payload):
        payload["email"] = ""

        with pytest.raises(ValidationError):
            schema.validate(payload)

    def test_it_raises_when_email_not_a_string(self, schema, payload):
        payload["email"] = {"foo": "bar"}

        with pytest.raises(ValidationError):
            schema.validate(payload)

    def test_it_raises_when_email_format_invalid(self, schema, payload):
        payload["email"] = "not-an-email"

        with pytest.raises(ValidationError):
            schema.validate(payload)

    def test_it_raises_when_email_too_long(self, schema, payload):
        payload["email"] = (
            "dagrun.bibianne.selen.asya."
            "dagrun.bibianne.selen.asya."
            "dagrun.bibianne.selen.asya."
            "dagrun.bibianne.selen.asya"
            "@foobar.com"
        )

        with pytest.raises(ValidationError):
            schema.validate(payload)

    def test_it_raises_when_display_name_not_a_string(self, schema, payload):
        payload["display_name"] = 42

        with pytest.raises(ValidationError):
            schema.validate(payload)

    def test_it_raises_when_display_name_too_long(self, schema, payload):
        payload["display_name"] = "Dagrun Bibianne Selen Asya Foobar"

        with pytest.raises(ValidationError):
            schema.validate(payload)

    def test_it_allows_missing_email_if_identities_present(self, schema, payload):
        payload["identities"] = [{"provider": "foo", "provider_unique_id": "bar"}]
        del payload["email"]

        schema.validate(payload)

    def test_it_allows_valid_identities(self, schema, payload):
        payload["identities"] = [{"provider": "foo", "provider_unique_id": "bar"}]

        appstruct = schema.validate(payload)

        assert "identities" in appstruct

    def test_it_raises_when_email_missing_and_identities_empty(self, schema, payload):
        del payload["email"]
        payload["identities"] = []

        with pytest.raises(ValidationError, match=".*identities.*too short.*"):
            schema.validate(payload)

    def test_it_raises_when_identities_not_an_array(self, schema, payload):
        payload["identities"] = "dragnabit"

        with pytest.raises(ValidationError, match=".*identities.*is not of type.*"):
            schema.validate(payload)

    def test_it_raises_when_identities_items_not_objects(self, schema, payload):
        payload["identities"] = ["flerp", "flop"]

        with pytest.raises(ValidationError, match=".*identities.*is not of type.*"):
            schema.validate(payload)

    def test_it_raises_when_provider_missing_in_identity(self, schema, payload):
        payload["identities"] = [{"foo": "bar", "provider_unique_id": "flop"}]

        with pytest.raises(
            ValidationError, match=".*provider'.*is a required property.*"
        ):
            schema.validate(payload)

    def test_it_raises_when_provider_unique_id_missing_in_identity(
        self, schema, payload
    ):
        payload["identities"] = [{"foo": "bar", "provider": "flop"}]

        with pytest.raises(
            ValidationError, match=".*provider_unique_id'.*is a required property.*"
        ):
            schema.validate(payload)

    def test_it_raises_if_identity_provider_is_not_a_string(self, schema, payload):
        payload["identities"] = [{"provider_unique_id": "bar", "provider": 75}]

        with pytest.raises(
            ValidationError, match=".*provider:.*is not of type.*string.*"
        ):
            schema.validate(payload)

    def test_it_raises_if_identity_provider_unique_id_is_not_a_string(
        self, schema, payload
    ):
        payload["identities"] = [{"provider_unique_id": [], "provider": "hithere"}]

        with pytest.raises(
            ValidationError, match=".*provider_unique_id:.*is not of type.*string.*"
        ):
            schema.validate(payload)

    @pytest.fixture
    def payload(self):
        return {
            "authority": "foobar.org",
            "username": "dagrun",
            "email": "dagrun@foobar.org",
            "display_name": "Dagrun Foobar",
        }

    @pytest.fixture
    def schema(self):
        return CreateUserAPISchema()


class TestUpdateUserAPISchema:
    def test_it_raises_when_email_empty(self, schema, payload):
        payload["email"] = ""

        with pytest.raises(ValidationError):
            schema.validate(payload)

    def test_it_raises_when_email_not_a_string(self, schema, payload):
        payload["email"] = {"foo": "bar"}

        with pytest.raises(ValidationError):
            schema.validate(payload)

    def test_it_raises_when_email_format_invalid(self, schema, payload):
        payload["email"] = "not-an-email"

        with pytest.raises(ValidationError):
            schema.validate(payload)

    def test_it_raises_when_email_too_long(self, schema, payload):
        payload["email"] = (
            "dagrun.bibianne.selen.asya."
            "dagrun.bibianne.selen.asya."
            "dagrun.bibianne.selen.asya."
            "dagrun.bibianne.selen.asya"
            "@foobar.com"
        )

        with pytest.raises(ValidationError):
            schema.validate(payload)

    def test_it_raises_when_display_name_not_a_string(self, schema, payload):
        payload["display_name"] = 42

        with pytest.raises(ValidationError):
            schema.validate(payload)

    def test_it_raises_when_display_name_too_long(self, schema, payload):
        payload["display_name"] = "Dagrun Bibianne Selen Asya Foobar"

        with pytest.raises(ValidationError):
            schema.validate(payload)

    def test_it_ignores_non_whitelisted_properties(self, schema):
        appstruct = schema.validate(
            {
                "display_name": "Full Name",
                "authority": "dangerous.biz",
                "orcid": "3094839jkfj",
            }
        )

        assert "display_name" in appstruct
        assert "authority" not in appstruct
        assert "orcid" not in appstruct

    @pytest.fixture
    def payload(self):
        return {"email": "dagrun@foobar.org", "display_name": "Dagrun Foobar"}

    @pytest.fixture
    def schema(self):
        return UpdateUserAPISchema()
