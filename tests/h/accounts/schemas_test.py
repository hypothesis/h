# -*- coding: utf-8 -*-
import colander
import pytest
from mock import Mock
from pyramid.exceptions import BadCSRFToken
from itsdangerous import BadData, SignatureExpired

from h.accounts import schemas


class FakeSerializer(object):
    def dumps(self, obj):
        return 'faketoken'

    def loads(self, token, max_age=0, return_timestamp=False):
        payload = {'username': 'foo@bar.com'}
        if return_timestamp:
            return payload, 1
        return payload


class FakeExpiredSerializer(FakeSerializer):
    def loads(self, token, max_age=0, return_timestamp=False):
        raise SignatureExpired("Token has expired")


class FakeInvalidSerializer(FakeSerializer):
    def loads(self, token, max_age=0, return_timestamp=False):
        raise BadData("Invalid token")


def test_unblacklisted_username(dummy_node):
    blacklist = set(['admin', 'root', 'postmaster'])

    # Should not raise for valid usernames
    schemas.unblacklisted_username(dummy_node, "john", blacklist)
    schemas.unblacklisted_username(dummy_node, "Abigail", blacklist)
    # Should raise for usernames in blacklist
    pytest.raises(colander.Invalid,
                  schemas.unblacklisted_username,
                  dummy_node,
                  "admin",
                  blacklist)
    # Should raise for case variants of usernames in blacklist
    pytest.raises(colander.Invalid,
                  schemas.unblacklisted_username,
                  dummy_node,
                  "PostMaster",
                  blacklist)


def test_unique_email_looks_up_user_by_email(dummy_node, pyramid_request, user_model):
    with pytest.raises(colander.Invalid):
        schemas.unique_email(dummy_node, "foo@bar.com")

    user_model.get_by_email.assert_called_with(pyramid_request.db, "foo@bar.com")


def test_unique_email_invalid_when_user_exists(dummy_node, user_model):
    pytest.raises(colander.Invalid,
                  schemas.unique_email,
                  dummy_node,
                  "foo@bar.com")


def test_unique_email_invalid_when_user_does_not_exist(dummy_node, user_model):
    user_model.get_by_email.return_value = None

    assert schemas.unique_email(dummy_node, "foo@bar.com") is None


def test_RegisterSchema_with_password_too_short(pyramid_request, user_model):
    schema = schemas.RegisterSchema().bind(request=pyramid_request)

    with pytest.raises(colander.Invalid) as exc:
        schema.deserialize({"password": "a"})
    assert exc.value.asdict()['password'] == "Shorter than minimum length 2"


def test_RegisterSchema_with_username_too_short(pyramid_request, user_model):
    schema = schemas.RegisterSchema().bind(request=pyramid_request)
    user_model.get_by_username.return_value = None

    with pytest.raises(colander.Invalid) as exc:
        schema.deserialize({"username": "a"})
    assert exc.value.asdict()['username'] == "Shorter than minimum length 3"


def test_RegisterSchema_with_username_too_long(pyramid_request, user_model):
    schema = schemas.RegisterSchema().bind(request=pyramid_request)
    user_model.get_by_username.return_value = None

    with pytest.raises(colander.Invalid) as exc:
        schema.deserialize({"username": "a" * 500})
    assert exc.value.asdict()['username'] == "Longer than maximum length 30"


def test_RegisterSchema_with_invalid_characters_in_username(pyramid_request,
                                                            user_model):
    user_model.get_by_username.return_value = None
    schema = schemas.RegisterSchema().bind(request=pyramid_request)

    with pytest.raises(colander.Invalid) as exc:
        schema.deserialize({"username": "Fred Flintstone"})
    assert exc.value.asdict()['username'] == ("Must contain only letters, "
                                              "numbers, periods, and "
                                              "underscores")


def test_ResetPasswordSchema_with_password_too_short(pyramid_csrf_request, user_model):
    schema = schemas.ResetPasswordSchema().bind(request=pyramid_csrf_request)

    with pytest.raises(colander.Invalid) as exc:
        schema.deserialize({"password": "a"})
    assert "password" in exc.value.asdict()


def test_LoginSchema_with_bad_csrf(pyramid_request, user_model):
    schema = schemas.LoginSchema().bind(request=pyramid_request)
    user = user_model.get_by_username.return_value
    user.is_activated = True

    with pytest.raises(BadCSRFToken):
        schema.deserialize({
            'username': 'jeannie',
            'password': 'cake',
        })


def test_LoginSchema_with_bad_username(pyramid_csrf_request, user_model):
    schema = schemas.LoginSchema().bind(request=pyramid_csrf_request)
    user_model.get_by_username.return_value = None
    user_model.get_by_email.return_value = None

    with pytest.raises(colander.Invalid) as exc:
        schema.deserialize({
            'username': 'jeannie',
            'password': 'cake',
        })

    assert 'username' in exc.value.asdict()


def test_LoginSchema_with_bad_password(pyramid_csrf_request, user_model):
    schema = schemas.LoginSchema().bind(request=pyramid_csrf_request)
    user_model.validate_user.return_value = False

    with pytest.raises(colander.Invalid) as exc:
        schema.deserialize({
            'username': 'jeannie',
            'password': 'cake',
        })

    assert 'password' in exc.value.asdict()


def test_LoginSchema_with_valid_request(pyramid_csrf_request, user_model):
    user = user_model.get_by_username.return_value
    user.is_activated = True

    schema = schemas.LoginSchema().bind(request=pyramid_csrf_request)

    assert 'user' in schema.deserialize({
        'username': 'jeannie',
        'password': 'cake',
    })


def test_LoginSchema_with_email_instead_of_username(pyramid_csrf_request, user_model):
    """If get_by_username() returns None it should try get_by_email()."""
    schema = schemas.LoginSchema().bind(request=pyramid_csrf_request)
    user_model.get_by_username.return_value = None
    user = user_model.get_by_email.return_value
    user.is_activated = True

    assert 'user' in schema.deserialize({
        'username': 'jeannie',
        'password': 'cake',
    })


def test_LoginSchema_with_inactive_user_account(pyramid_csrf_request, user_model):
    user = user_model.get_by_username.return_value
    user.is_activated = False
    schema = schemas.LoginSchema().bind(request=pyramid_csrf_request)

    with pytest.raises(colander.Invalid) as exc:
        schema.deserialize({
            'username': 'jeannie',
            'password': 'cake',
        })

    assert ("You haven't activated your account yet" in
            exc.value.asdict().get('username', ''))


def test_ForgotPasswordSchema_invalid_with_no_user(pyramid_csrf_request, user_model):
    schema = schemas.ForgotPasswordSchema().bind(request=pyramid_csrf_request)
    user_model.get_by_email.return_value = None

    with pytest.raises(colander.Invalid) as exc:
        schema.deserialize({'email': 'rapha@example.com'})

    assert 'email' in exc.value.asdict()
    assert exc.value.asdict()['email'] == 'Unknown email address'


def test_ForgotPasswordSchema_adds_user_to_appstruct(pyramid_csrf_request, user_model):
    schema = schemas.ForgotPasswordSchema().bind(request=pyramid_csrf_request)
    user = user_model.get_by_email.return_value

    appstruct = schema.deserialize({'email': 'rapha@example.com'})

    assert appstruct['user'] == user


def test_ResetPasswordSchema_with_invalid_user_token(pyramid_csrf_request, user_model):
    pyramid_csrf_request.registry.password_reset_serializer = FakeInvalidSerializer()
    schema = schemas.ResetPasswordSchema().bind(request=pyramid_csrf_request)

    with pytest.raises(colander.Invalid) as exc:
        schema.deserialize({
            'user': 'abc123',
            'password': 'secret',
        })

    assert 'user' in exc.value.asdict()
    assert 'reset code is not valid' in exc.value.asdict()['user']


def test_ResetPasswordSchema_with_expired_token(pyramid_csrf_request, user_model):
    pyramid_csrf_request.registry.password_reset_serializer = FakeExpiredSerializer()
    schema = schemas.ResetPasswordSchema().bind(request=pyramid_csrf_request)

    with pytest.raises(colander.Invalid) as exc:
        schema.deserialize({
            'user': 'abc123',
            'password': 'secret',
        })

    assert 'user' in exc.value.asdict()
    assert 'reset code has expired' in exc.value.asdict()['user']


@pytest.mark.usefixtures('user_model')
def test_ResetPasswordSchema_user_has_already_reset_their_password(pyramid_csrf_request,
                                                                   user_model):
    pyramid_csrf_request.registry.password_reset_serializer = FakeSerializer()
    schema = schemas.ResetPasswordSchema().bind(request=pyramid_csrf_request)
    user = user_model.get_by_username.return_value
    user.password_updated = 2

    with pytest.raises(colander.Invalid) as exc:
        schema.deserialize({
            'user': 'abc123',
            'password': 'secret',
        })

    assert 'user' in exc.value.asdict()
    assert 'already reset your password' in exc.value.asdict()['user']


@pytest.mark.usefixtures('user_model')
def test_ResetPasswordSchema_adds_user_to_appstruct(pyramid_csrf_request, user_model):
    pyramid_csrf_request.registry.password_reset_serializer = FakeSerializer()
    schema = schemas.ResetPasswordSchema().bind(request=pyramid_csrf_request)
    user = user_model.get_by_username.return_value
    user.password_updated = 0

    appstruct = schema.deserialize({
        'user': 'abc123',
        'password': 'secret',
    })

    assert appstruct['user'] == user


def test_EmailChangeSchema_rejects_non_matching_emails(pyramid_csrf_request, user_model):
    user = Mock()
    pyramid_csrf_request.authenticated_user = user
    schema = schemas.EmailChangeSchema().bind(request=pyramid_csrf_request)
    # The email isn't taken
    user_model.get_by_email.return_value = None

    with pytest.raises(colander.Invalid) as exc:
        schema.deserialize({'email': 'foo@bar.com',
                            'email_confirm': 'foo@baz.com',
                            'password': 'flibble'})

    assert 'email_confirm' in exc.value.asdict()


def test_EmailChangeSchema_rejects_wrong_password(pyramid_csrf_request, user_model):
    user = Mock()
    pyramid_csrf_request.authenticated_user = user
    schema = schemas.EmailChangeSchema().bind(request=pyramid_csrf_request)
    # The email isn't taken
    user_model.get_by_email.return_value = None
    # The password does not check out
    user_model.validate_user.return_value = False

    with pytest.raises(colander.Invalid) as exc:
        schema.deserialize({'email': 'foo@bar.com',
                            'email_confirm': 'foo@bar.com',
                            'password': 'flibble'})

    user_model.validate_user.assert_called_once_with(user, 'flibble')
    assert 'password' in exc.value.asdict()


def test_PasswordChangeSchema_rejects_non_matching_passwords(pyramid_csrf_request,
                                                             user_model):
    user = Mock()
    pyramid_csrf_request.authenticated_user = user
    schema = schemas.PasswordChangeSchema().bind(request=pyramid_csrf_request)

    with pytest.raises(colander.Invalid) as exc:
        schema.deserialize({'new_password': 'wibble',
                            'new_password_confirm': 'wibble!',
                            'password': 'flibble'})

    assert 'new_password_confirm' in exc.value.asdict()


def test_PasswordChangeSchema_rejects_wrong_password(pyramid_csrf_request, user_model):
    user = Mock()
    pyramid_csrf_request.authenticated_user = user
    schema = schemas.PasswordChangeSchema().bind(request=pyramid_csrf_request)
    # The password does not check out
    user_model.validate_user.return_value = False

    with pytest.raises(colander.Invalid) as exc:
        schema.deserialize({'new_password': 'wibble',
                            'new_password_confirm': 'wibble!',
                            'password': 'flibble'})

    user_model.validate_user.assert_called_once_with(user, 'flibble')
    assert 'password' in exc.value.asdict()


@pytest.fixture
def activation_model(patch):
    return patch('h.accounts.schemas.models.Activation')


@pytest.fixture
def dummy_node(pyramid_request):
    class DummyNode(object):
        def __init__(self, request):
            self.bindings = {
                'request': request
            }
    return DummyNode(pyramid_request)


@pytest.fixture
def user_model(patch):
    return patch('h.accounts.schemas.models.User')
