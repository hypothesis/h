from unittest.mock import Mock

import colander
import pytest
from pyramid.exceptions import BadCSRFToken

from h.schemas.forms.accounts import LoginSchema
from h.services.user import UserNotActivated
from h.services.user_password import UserPasswordService


@pytest.mark.usefixtures("user_service", "user_password_service")
class TestLoginSchema:
    def test_passes_username_to_user_service(
        self, factories, pyramid_csrf_request, user_service
    ):
        user = factories.User.build(username="jeannie")
        user_service.fetch_for_login.return_value = user
        schema = LoginSchema().bind(request=pyramid_csrf_request)

        schema.deserialize({"username": "jeannie", "password": "cake"})

        user_service.fetch_for_login.assert_called_once_with(
            username_or_email="jeannie"
        )

    def test_passes_password_to_user_password_service(
        self, factories, pyramid_csrf_request, user_service, user_password_service
    ):
        user = factories.User.build(username="jeannie")
        user_service.fetch_for_login.return_value = user
        schema = LoginSchema().bind(request=pyramid_csrf_request)

        schema.deserialize({"username": "jeannie", "password": "cake"})

        user_password_service.check_password.assert_called_once_with(user, "cake")

    def test_it_returns_user_when_valid(
        self, factories, pyramid_csrf_request, user_service
    ):
        user = factories.User.build(username="jeannie")
        user_service.fetch_for_login.return_value = user
        schema = LoginSchema().bind(request=pyramid_csrf_request)

        result = schema.deserialize({"username": "jeannie", "password": "cake"})

        assert result["user"] is user

    def test_invalid_with_bad_csrf(self, pyramid_request):
        schema = LoginSchema().bind(request=pyramid_request)

        with pytest.raises(BadCSRFToken):
            schema.deserialize({"username": "jeannie", "password": "cake"})

    def test_invalid_with_inactive_user(self, pyramid_csrf_request, user_service):
        schema = LoginSchema().bind(request=pyramid_csrf_request)
        user_service.fetch_for_login.side_effect = UserNotActivated()

        with pytest.raises(colander.Invalid) as exc:
            schema.deserialize({"username": "jeannie", "password": "cake"})
        errors = exc.value.asdict()

        assert "username" in errors
        assert "activate your account" in errors["username"]

    def test_invalid_with_unknown_user(self, pyramid_csrf_request, user_service):
        schema = LoginSchema().bind(request=pyramid_csrf_request)
        user_service.fetch_for_login.return_value = None

        with pytest.raises(colander.Invalid) as exc:
            schema.deserialize({"username": "jeannie", "password": "cake"})
        errors = exc.value.asdict()

        assert "username" in errors
        assert "does not exist" in errors["username"]

    def test_invalid_with_bad_password(
        self, factories, pyramid_csrf_request, user_service, user_password_service
    ):
        user = factories.User.build(username="jeannie")
        user_service.fetch_for_login.return_value = user
        user_password_service.check_password.return_value = False
        schema = LoginSchema().bind(request=pyramid_csrf_request)

        with pytest.raises(colander.Invalid) as exc:
            schema.deserialize({"username": "jeannie", "password": "cake"})
        errors = exc.value.asdict()

        assert "password" in errors
        assert "Wrong password" in errors["password"]

    @pytest.mark.parametrize(
        "params,value",
        [
            # If a ?username=foobob query param is given then the username field in
            # the login form is pre-filled with "foobob".
            ({"username": "foobob"}, "foobob"),
            # If the foobob query param is missing or has no value then the
            # username field isn't pre-filled.
            ({"username": ""}, ""),
            ({}, ""),
        ],
    )
    def test_default_values_prefills_username_from_username_query_param(
        self, pyramid_request, params, value
    ):
        pyramid_request.params = params

        assert LoginSchema.default_values(pyramid_request)["username"] == value


@pytest.fixture
def user_password_service(pyramid_config):
    service = Mock(spec_set=UserPasswordService())
    service.check_password.return_value = True
    pyramid_config.register_service(service, name="user_password")
    return service
