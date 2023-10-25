from datetime import datetime, timedelta
from unittest.mock import create_autospec

import colander
import pytest
import pytz
from itsdangerous import BadData, SignatureExpired, URLSafeTimedSerializer

from h.schemas.forms.accounts import ResetPasswordSchema


@pytest.mark.usefixtures("pyramid_config")
class TestResetPasswordSchemaDeserialize:
    def test_it_is_valid_with_a_long_password(self, schema):
        # Yeah... our minimum password length is 8 chars. See
        # `h.schema.forms.accounts.util`
        schema.deserialize({"user": "*any*", "password": "new-password"})

    @pytest.mark.parametrize("password", ("", "a"))
    def test_it_is_invalid_with_password_too_short(self, schema, password):
        with pytest.raises(colander.Invalid) as exc:
            schema.deserialize({"user": "*any*", "password": password})

        assert "password" in exc.value.asdict()

    def test_it_is_invalid_with_a_null_user(self, schema):
        with pytest.raises(colander.Invalid) as exc:
            schema.deserialize({"user": colander.null, "password": "new-password"})

        assert "user" in exc.value.asdict()

    def test_it_is_invalid_with_a_missing_user(self, schema, models):
        models.User.get_by_username.return_value = None

        with pytest.raises(colander.Invalid) as exc:
            schema.deserialize({"user": "encoded_token", "password": "new-password"})

        assert "user" in exc.value.asdict()

    def test_it_is_invalid_with_invalid_user_token(self, schema, serializer):
        serializer.loads.side_effect = BadData("Invalid token")

        with pytest.raises(colander.Invalid) as exc:
            schema.deserialize({"user": "INVALID_TOKEN", "password": "new-password"})

        assert "user" in exc.value.asdict()
        assert "Wrong reset code." in exc.value.asdict()["user"]

    def test_it_is_invalid_with_expired_token(self, schema, serializer):
        serializer.loads.side_effect = SignatureExpired("Token has expired")

        with pytest.raises(colander.Invalid) as exc:
            schema.deserialize({"user": "encoded_token", "password": "new-password"})

        serializer.loads.assert_called_once_with(
            "encoded_token", max_age=72 * 3600, return_timestamp=True
        )

        assert "user" in exc.value.asdict()
        assert "Reset code has expired." in exc.value.asdict()["user"]

    @pytest.mark.parametrize(
        "password_updated",
        (
            # This situation triggers if the users password has not been used since
            # the token was issued. Note our DB dates are not timezone aware.
            datetime.now() - timedelta(days=1),
            # ... or if it's never been reset
            None,
        ),
    )
    def test_it_returns_user_when_valid(
        self, schema, user, models, password_updated, pyramid_csrf_request, serializer
    ):
        user.password_updated = password_updated

        appstruct = schema.deserialize(
            {"user": "encoded_token", "password": "new-password"}
        )

        models.User.get_by_username.assert_called_once_with(
            pyramid_csrf_request.db,
            serializer.loads.return_value[0],
            pyramid_csrf_request.default_authority,
        )
        assert appstruct["user"] == user

    def test_it_is_invalid_if_user_has_already_reset_their_password(self, schema, user):
        # This situation triggers if the users password has been used since
        # the token was issued. Note our DB dates are not timezone aware.
        user.password_updated = datetime.now() + timedelta(days=1)

        with pytest.raises(colander.Invalid) as exc:
            schema.deserialize({"user": "EXPIRED_TOKEN", "password": "new-password"})

        assert "user" in exc.value.asdict()
        assert "This reset code has already been used." in exc.value.asdict()["user"]

    @pytest.fixture
    def schema(self, pyramid_csrf_request):
        return ResetPasswordSchema().bind(request=pyramid_csrf_request)

    @pytest.fixture(autouse=True)
    def serializer(
        self, pyramid_csrf_request, pyramid_config
    ):  # pylint:disable=unused-argument
        # We must be after `pyramid_config` in the queue, as it replaces the
        # registry object with another one which undoes our changes here

        serializer = create_autospec(
            URLSafeTimedSerializer, instance=True, spec_set=True
        )

        # Note that dates from `URLSafeTimedSerializer` are timezone aware
        now = datetime.now(tz=pytz.UTC)
        serializer.loads.return_value = "username@example.com", now

        pyramid_csrf_request.registry.password_reset_serializer = serializer

        return serializer

    @pytest.fixture(autouse=True)
    def models(self, patch):
        return patch("h.schemas.forms.accounts.reset_password.models")

    @pytest.fixture(autouse=True)
    def user(self, models):
        user = models.User.get_by_username.return_value
        user.password_updated = None
        return user
