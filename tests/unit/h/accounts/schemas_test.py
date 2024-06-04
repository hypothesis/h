from datetime import datetime, timedelta
from unittest.mock import Mock

import colander
import pytest
from pyramid.exceptions import BadCSRFToken

from h.accounts import schemas
from h.services.user_password import UserPasswordService
from h.util.user import format_userid

pytestmark = pytest.mark.usefixtures("pyramid_config")


class TestUnblacklistedUsername:
    def test(self, dummy_node):
        blacklist = {"admin", "root", "postmaster"}

        # Should not raise for valid usernames
        schemas.unblacklisted_username(dummy_node, "john", blacklist)
        schemas.unblacklisted_username(dummy_node, "Abigail", blacklist)
        # Should raise for usernames in blacklist
        pytest.raises(
            colander.Invalid,
            schemas.unblacklisted_username,
            dummy_node,
            "admin",
            blacklist,
        )
        # Should raise for case variants of usernames in blacklist
        pytest.raises(
            colander.Invalid,
            schemas.unblacklisted_username,
            dummy_node,
            "PostMaster",
            blacklist,
        )


@pytest.mark.usefixtures("user_model")
class TestUniqueEmail:
    def test_it_looks_up_user_by_email(self, dummy_node, pyramid_request, user_model):
        with pytest.raises(colander.Invalid):
            schemas.unique_email(dummy_node, "foo@bar.com")

        user_model.get_by_email.assert_called_with(
            pyramid_request.db, "foo@bar.com", pyramid_request.default_authority
        )

    def test_it_is_invalid_when_user_exists(self, dummy_node):
        pytest.raises(colander.Invalid, schemas.unique_email, dummy_node, "foo@bar.com")

    def test_it_is_valid_when_user_does_not_exist(self, dummy_node, user_model):
        user_model.get_by_email.return_value = None

        assert schemas.unique_email(dummy_node, "foo@bar.com") is None

    def test_it_is_valid_when_authorized_users_email(
        self, dummy_node, pyramid_config, user_model
    ):
        """
        If the given email is the authorized user's current email it's valid.

        This is so that we don't get a "That email is already taken" validation
        error when a user tries to change their email address to the same email
        address that they already have it set to.

        """
        pyramid_config.testing_securitypolicy("acct:elliot@hypothes.is")
        user_model.get_by_email.return_value = Mock(
            spec_set=("userid",), userid="acct:elliot@hypothes.is"
        )

        schemas.unique_email(dummy_node, "elliot@bar.com")


class TestRegisterSchema:
    def test_it_is_invalid_when_password_too_short(self, pyramid_request):
        schema = schemas.RegisterSchema().bind(request=pyramid_request)

        with pytest.raises(colander.Invalid) as exc:
            schema.deserialize({"password": "a"})
        assert exc.value.asdict()["password"] == ("Must be 8 characters or more.")

    def test_it_is_invalid_when_username_too_short(self, pyramid_request):
        schema = schemas.RegisterSchema().bind(request=pyramid_request)

        with pytest.raises(colander.Invalid) as exc:
            schema.deserialize({"username": "a"})
        assert exc.value.asdict()["username"] == ("Must be 3 characters or more.")

    def test_it_is_invalid_when_username_too_long(self, pyramid_request):
        schema = schemas.RegisterSchema().bind(request=pyramid_request)

        with pytest.raises(colander.Invalid) as exc:
            schema.deserialize({"username": "a" * 500})
        assert exc.value.asdict()["username"] == ("Must be 30 characters or less.")

    def test_it_is_invalid_with_invalid_characters_in_username(self, pyramid_request):
        schema = schemas.RegisterSchema().bind(request=pyramid_request)

        with pytest.raises(colander.Invalid) as exc:
            schema.deserialize({"username": "Fred Flintstone"})
        assert exc.value.asdict()["username"] == (
            "Must have only letters, " "numbers, periods, and " "underscores."
        )

    def test_it_is_invalid_with_false_privacy_accepted(self, pyramid_request):
        schema = schemas.RegisterSchema().bind(request=pyramid_request)

        with pytest.raises(colander.Invalid) as exc:
            schema.deserialize({"privacy_accepted": "false"})

        assert (
            exc.value.asdict()["privacy_accepted"]
            == "Acceptance of the privacy policy is required"
        )

    def test_it_is_invalid_when_privacy_accepted_missing(self, pyramid_request):
        schema = schemas.RegisterSchema().bind(request=pyramid_request)

        with pytest.raises(colander.Invalid) as exc:
            schema.deserialize({})

        assert exc.value.asdict()["privacy_accepted"] == "Required"

    def test_it_is_invalid_when_user_recently_deleted(
        self, factories, pyramid_request, valid_params
    ):
        """If an account with the same username was recently deleted it should be invalid."""
        schema = schemas.RegisterSchema().bind(request=pyramid_request)
        factories.UserDeletion(
            userid=format_userid(
                username=valid_params["username"],
                authority=pyramid_request.default_authority,
            )
        )

        with pytest.raises(colander.Invalid) as exc:
            schema.deserialize(valid_params)

        assert exc.value.asdict() == {"username": "This username is already taken."}

    def test_it_validates_with_valid_payload(
        self, pyramid_csrf_request, valid_params, factories
    ):
        schema = schemas.RegisterSchema().bind(request=pyramid_csrf_request)
        # A user with the same username was deleted over a month ago.
        # This should not prevent registration.
        factories.UserDeletion(
            userid=format_userid(
                valid_params["username"], pyramid_csrf_request.default_authority
            ),
            requested_at=datetime.now() - timedelta(days=32),
        )

        result = schema.deserialize(valid_params)

        assert result == dict(
            valid_params, privacy_accepted=True, comms_opt_in=None, csrf_token=None
        )

    @pytest.fixture
    def valid_params(self):
        return {
            "username": "filbert",
            "email": "foo@bar.com",
            "password": "sdlkfjlk3j3iuei",
            "privacy_accepted": "true",
        }


@pytest.mark.usefixtures("models", "user_password_service")
class TestEmailChangeSchema:
    def test_it_returns_the_new_email_when_valid(self, schema):
        appstruct = schema.deserialize({"email": "foo@bar.com", "password": "flibble"})

        assert appstruct["email"] == "foo@bar.com"

    def test_it_is_valid_if_email_same_as_users_existing_email(
        self, schema, user, models, pyramid_config
    ):
        """
        It is valid if the new email is the same as the user's existing one.

        Trying to change your email to what your email already is should not
        return an error.

        """
        models.User.get_by_email.return_value = Mock(
            spec_set=["userid"], userid=user.userid
        )
        pyramid_config.testing_securitypolicy(user.userid)

        schema.deserialize({"email": user.email, "password": "flibble"})

    def test_it_is_invalid_if_csrf_token_missing(self, pyramid_request, schema):
        del pyramid_request.headers["X-CSRF-Token"]

        with pytest.raises(BadCSRFToken):
            schema.deserialize({"email": "foo@bar.com", "password": "flibble"})

    def test_it_is_invalid_if_csrf_token_wrong(self, pyramid_request, schema):
        pyramid_request.headers["X-CSRF-Token"] = "WRONG"

        with pytest.raises(BadCSRFToken):
            schema.deserialize({"email": "foo@bar.com", "password": "flibble"})

    def test_it_is_invalid_if_password_wrong(self, schema, user_password_service):
        user_password_service.check_password.return_value = False

        with pytest.raises(colander.Invalid) as exc:
            schema.deserialize({"email": "foo@bar.com", "password": "WRONG"})

        assert exc.value.asdict() == {"password": "Wrong password."}

    def test_it_returns_incorrect_password_error_if_password_too_short(
        self, schema, user_password_service
    ):
        """
        The schema should be invalid if the password is too short.

        Test that this returns a "that was not the right password" error rather
        than a "that password is too short error" as it used to (the user is
        entering their current password for authentication, they aren't
        choosing a new password).

        """
        user_password_service.check_password.return_value = False

        with pytest.raises(colander.Invalid) as exc:
            schema.deserialize(
                {
                    "email": "foo@bar.com",
                    "password": "a",  # Too short to be a valid password.
                }
            )

        assert exc.value.asdict() == {"password": "Wrong password."}

    def test_it_is_invalid_if_email_too_long(self, schema):
        with pytest.raises(colander.Invalid) as exc:
            schema.deserialize({"email": "a" * 100 + "@bar.com", "password": "flibble"})

        assert exc.value.asdict() == {"email": "Must be 100 characters or less."}

    def test_it_is_invalid_if_email_not_a_valid_email_address(self, schema):
        with pytest.raises(colander.Invalid) as exc:
            schema.deserialize(
                {"email": "this is not a valid email address", "password": "flibble"}
            )

        assert exc.value.asdict() == {"email": "Invalid email address."}

    def test_it_is_invalid_if_email_already_taken(self, models, schema):
        models.User.get_by_email.return_value = Mock(spec_set=["userid"])

        with pytest.raises(colander.Invalid) as exc:
            schema.deserialize({"email": "foo@bar.com", "password": "flibble"})

        assert exc.value.asdict() == {
            "email": "Sorry, an account with this " "email address already exists."
        }

    @pytest.fixture
    def pyramid_request(self, pyramid_csrf_request, user):
        pyramid_csrf_request.user = user
        return pyramid_csrf_request

    @pytest.fixture
    def schema(self, pyramid_request):
        return schemas.EmailChangeSchema().bind(request=pyramid_request)

    @pytest.fixture
    def user(self, factories):
        return factories.User.build()

    @pytest.fixture
    def models(self, patch):
        models = patch("h.accounts.schemas.models")

        # By default there isn't already an account with the email address that
        # we're trying to change to.
        models.User.get_by_email.return_value = None

        return models


@pytest.mark.usefixtures("user_password_service")
class TestPasswordChangeSchema:
    def test_it_is_invalid_if_passwords_dont_match(self, pyramid_csrf_request):
        user = Mock()
        pyramid_csrf_request.user = user
        schema = schemas.PasswordChangeSchema().bind(request=pyramid_csrf_request)

        with pytest.raises(colander.Invalid) as exc:
            schema.deserialize(
                {
                    "new_password": "foo-bar-baz",
                    "new_password_confirm": "foo-bar-buzz",
                    "password": "flibble",
                }
            )

        assert "new_password_confirm" in exc.value.asdict()

    def test_it_is_invalid_if_current_password_is_wrong(
        self, pyramid_csrf_request, user_password_service
    ):
        user = Mock()
        pyramid_csrf_request.user = user
        schema = schemas.PasswordChangeSchema().bind(request=pyramid_csrf_request)
        user_password_service.check_password.return_value = False

        with pytest.raises(colander.Invalid) as exc:
            schema.deserialize(
                {
                    "new_password": "foo-bar-baz",
                    "new_password_confirm": "foo-bar-baz",
                    "password": "flibble",
                }
            )

        user_password_service.check_password.assert_called_once_with(user, "flibble")
        assert "password" in exc.value.asdict()


@pytest.mark.usefixtures("user_password_service")
class TestDeleteAccountSchema:
    def test_it(self, schema, user, user_password_service):
        user_password_service.check_password.return_value = True

        schema.deserialize({"password": "test_password"})

        user_password_service.check_password.assert_called_once_with(
            user, "test_password"
        )

    @pytest.mark.parametrize(
        "password,expected_error_dict",
        [
            ("wrong_password", {"password": "Wrong password."}),
            ("", {"password": "Required"}),
            (None, {"password": "Required"}),
        ],
    )
    def test_it_when_the_password_is_wrong(
        self, schema, user_password_service, password, expected_error_dict
    ):
        user_password_service.check_password.return_value = False

        with pytest.raises(colander.Invalid) as exc_info:
            schema.deserialize({"password": password})

        assert exc_info.value.asdict() == expected_error_dict

    def test_it_when_the_password_is_missing(self, schema, user_password_service):
        user_password_service.check_password.return_value = False

        with pytest.raises(colander.Invalid) as exc_info:
            schema.deserialize({})

        assert exc_info.value.asdict() == {"password": "Required"}

    @pytest.fixture
    def user(self, factories):
        return factories.User()

    @pytest.fixture
    def pyramid_csrf_request(self, pyramid_csrf_request, user):
        pyramid_csrf_request.user = user
        return pyramid_csrf_request

    @pytest.fixture
    def schema(self, pyramid_csrf_request):
        return schemas.DeleteAccountSchema().bind(request=pyramid_csrf_request)


@pytest.fixture
def dummy_node(pyramid_request):
    class DummyNode:
        def __init__(self, request):
            self.bindings = {"request": request}

    return DummyNode(pyramid_request)


@pytest.fixture
def user_model(patch):
    return patch("h.accounts.schemas.models.User")


@pytest.fixture
def user_password_service(pyramid_config):
    service = Mock(spec_set=UserPasswordService())
    service.check_password.return_value = True
    pyramid_config.register_service(service, name="user_password")
    return service
