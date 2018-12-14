# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import colander
import pytest
from itsdangerous import BadData, SignatureExpired

from h.schemas.forms.accounts import ResetPasswordSchema


@pytest.mark.usefixtures("user_model")
class TestResetPasswordSchema(object):
    def test_it_is_invalid_with_password_too_short(self, pyramid_csrf_request):
        schema = ResetPasswordSchema().bind(request=pyramid_csrf_request)

        with pytest.raises(colander.Invalid) as exc:
            schema.deserialize({"password": "a"})
        assert "password" in exc.value.asdict()

    def test_it_is_invalid_with_invalid_user_token(self, pyramid_csrf_request):
        pyramid_csrf_request.registry.password_reset_serializer = (
            self.FakeInvalidSerializer()
        )
        schema = ResetPasswordSchema().bind(request=pyramid_csrf_request)

        with pytest.raises(colander.Invalid) as exc:
            schema.deserialize({"user": "abc123", "password": "secret"})

        assert "user" in exc.value.asdict()
        assert "Wrong reset code." in exc.value.asdict()["user"]

    def test_it_is_invalid_with_expired_token(self, pyramid_csrf_request):
        pyramid_csrf_request.registry.password_reset_serializer = (
            self.FakeExpiredSerializer()
        )
        schema = ResetPasswordSchema().bind(request=pyramid_csrf_request)

        with pytest.raises(colander.Invalid) as exc:
            schema.deserialize({"user": "abc123", "password": "secret"})

        assert "user" in exc.value.asdict()
        assert "Reset code has expired." in exc.value.asdict()["user"]

    def test_it_is_invalid_if_user_has_already_reset_their_password(
        self, pyramid_csrf_request, user_model
    ):
        pyramid_csrf_request.registry.password_reset_serializer = self.FakeSerializer()
        schema = ResetPasswordSchema().bind(request=pyramid_csrf_request)
        user = user_model.get_by_username.return_value
        user.password_updated = 2

        with pytest.raises(colander.Invalid) as exc:
            schema.deserialize({"user": "abc123", "password": "secret"})

        assert "user" in exc.value.asdict()
        assert "This reset code has already been used." in exc.value.asdict()["user"]

    def test_it_returns_user_when_valid(self, pyramid_csrf_request, user_model):
        pyramid_csrf_request.registry.password_reset_serializer = self.FakeSerializer()
        schema = ResetPasswordSchema().bind(request=pyramid_csrf_request)
        user = user_model.get_by_username.return_value
        user.password_updated = 0

        appstruct = schema.deserialize({"user": "abc123", "password": "secret"})

        assert appstruct["user"] == user

    class FakeSerializer(object):
        def dumps(self, obj):
            return "faketoken"

        def loads(self, token, max_age=0, return_timestamp=False):
            payload = {"username": "foo@bar.com"}
            if return_timestamp:
                return payload, 1
            return payload

    class FakeExpiredSerializer(FakeSerializer):
        def loads(self, token, max_age=0, return_timestamp=False):
            raise SignatureExpired("Token has expired")

    class FakeInvalidSerializer(FakeSerializer):
        def loads(self, token, max_age=0, return_timestamp=False):
            raise BadData("Invalid token")


@pytest.fixture
def user_model(patch):
    return patch("h.accounts.schemas.models.User")
