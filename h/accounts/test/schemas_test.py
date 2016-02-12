# -*- coding: utf-8 -*-
import colander
import pytest
from mock import Mock
from mock import patch
from pyramid.exceptions import BadCSRFToken
from pyramid.testing import DummyRequest
from itsdangerous import BadData, SignatureExpired

from h.accounts import schemas


class DummyNode(object):
    pass


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


def csrf_request(config, **kwargs):
    request = DummyRequest(registry=config.registry, **kwargs)
    request.headers['X-CSRF-Token'] = request.session.get_csrf_token()
    return request


def test_unblacklisted_username(config):
    request = DummyRequest()
    node = colander.SchemaNode(colander.String()).bind(request=request)
    blacklist = set(['admin', 'root', 'postmaster'])

    # Should not raise for valid usernames
    schemas.unblacklisted_username(node, "john", blacklist)
    schemas.unblacklisted_username(node, "Abigail", blacklist)
    # Should raise for usernames in blacklist
    pytest.raises(colander.Invalid,
                  schemas.unblacklisted_username,
                  node,
                  "admin",
                  blacklist)
    # Should raise for case variants of usernames in blacklist
    pytest.raises(colander.Invalid,
                  schemas.unblacklisted_username,
                  node,
                  "PostMaster",
                  blacklist)


def test_unique_email_looks_up_user_by_email(user_model):
    node = DummyNode()

    with pytest.raises(colander.Invalid):
        schemas.unique_email(node, "foo@bar.com")

    user_model.get_by_email.assert_called_with("foo@bar.com")


def test_unique_email_invalid_when_user_exists(user_model):
    node = DummyNode()

    pytest.raises(colander.Invalid,
                  schemas.unique_email,
                  node,
                  "foo@bar.com")


def test_unique_email_invalid_when_user_does_not_exist(user_model):
    node = DummyNode()
    user_model.get_by_email.return_value = None

    assert schemas.unique_email(node, "foo@bar.com") is None


def test_RegisterSchema_with_password_too_short(user_model):
    schema = schemas.RegisterSchema().bind(request=DummyRequest())

    with pytest.raises(colander.Invalid) as err:
        schema.deserialize({"password": "a"})
    assert "password" in err.value.asdict()


def test_RegisterSchema_with_username_too_short(user_model):
    schema = schemas.RegisterSchema().bind(request=DummyRequest())

    with pytest.raises(colander.Invalid) as err:
        schema.deserialize({"username": "a"})
    assert "username" in err.value.asdict()


def test_RegisterSchema_with_username_too_long(user_model):
    schema = schemas.RegisterSchema().bind(request=DummyRequest())

    with pytest.raises(colander.Invalid) as err:
        schema.deserialize({"username": "a" * 500})
    assert "username" in err.value.asdict()


def test_ResetPasswordSchema_with_password_too_short(config, user_model):
    schema = schemas.ResetPasswordSchema().bind(request=csrf_request(config))

    with pytest.raises(colander.Invalid) as err:
        schema.deserialize({"password": "a"})
    assert "password" in err.value.asdict()


def test_LoginSchema_with_bad_csrf(config, user_model):
    request = DummyRequest()
    schema = schemas.LoginSchema().bind(request=request)
    user = user_model.get_by_username.return_value
    user.is_activated = True

    with pytest.raises(BadCSRFToken):
        schema.deserialize({
            'username': 'jeannie',
            'password': 'cake',
        })


def test_LoginSchema_with_bad_username(config, user_model):
    request = csrf_request(config)
    schema = schemas.LoginSchema().bind(request=request)
    user_model.get_by_username.return_value = None
    user_model.get_by_email.return_value = None

    with pytest.raises(colander.Invalid) as exc:
        schema.deserialize({
            'username': 'jeannie',
            'password': 'cake',
        })

    assert 'username' in exc.value.asdict()


def test_LoginSchema_with_bad_password(config, user_model):
    request = csrf_request(config)
    schema = schemas.LoginSchema().bind(request=request)
    user_model.validate_user.return_value = False

    with pytest.raises(colander.Invalid) as exc:
        schema.deserialize({
            'username': 'jeannie',
            'password': 'cake',
        })

    assert 'password' in exc.value.asdict()


def test_LoginSchema_with_valid_request(config, user_model):
    request = csrf_request(config)
    user = user_model.get_by_username.return_value
    user.is_activated = True

    schema = schemas.LoginSchema().bind(request=request)

    assert 'user' in schema.deserialize({
        'username': 'jeannie',
        'password': 'cake',
    })


def test_LoginSchema_with_email_instead_of_username(config, user_model):
    """If get_by_username() returns None it should try get_by_email()."""
    request = csrf_request(config)
    schema = schemas.LoginSchema().bind(request=request)
    user_model.get_by_username.return_value = None
    user = user_model.get_by_email.return_value
    user.is_activated = True

    assert 'user' in schema.deserialize({
        'username': 'jeannie',
        'password': 'cake',
    })


def test_LoginSchema_with_inactive_user_account(config, user_model):
    request = csrf_request(config)
    user = user_model.get_by_username.return_value
    user.is_activated = False
    schema = schemas.LoginSchema().bind(request=request)

    with pytest.raises(colander.Invalid) as exc:
        schema.deserialize({
            'username': 'jeannie',
            'password': 'cake',
        })

    assert ("You haven't activated your account yet" in
            exc.value.asdict().get('username', ''))


def test_ForgotPasswordSchema_invalid_with_no_user(config, user_model):
    request = csrf_request(config)
    schema = schemas.ForgotPasswordSchema().bind(request=request)
    user_model.get_by_email.return_value = None

    with pytest.raises(colander.Invalid) as exc:
        schema.deserialize({'email': 'rapha@example.com'})

    assert 'email' in exc.value.asdict()
    assert 'no user with the email address' in exc.value.asdict()['email']


def test_ForgotPasswordSchema_adds_user_to_appstruct(config, user_model):
    request = csrf_request(config)
    schema = schemas.ForgotPasswordSchema().bind(request=request)
    user = user_model.get_by_email.return_value

    appstruct = schema.deserialize({'email': 'rapha@example.com'})

    assert appstruct['user'] == user


def test_ResetPasswordSchema_with_invalid_user_token(config, user_model):
    request = csrf_request(config)
    request.registry.password_reset_serializer = FakeInvalidSerializer()
    schema = schemas.ResetPasswordSchema().bind(request=request)

    with pytest.raises(colander.Invalid) as exc:
        schema.deserialize({
            'user': 'abc123',
            'password': 'secret',
        })

    assert 'user' in exc.value.asdict()
    assert 'reset code is not valid' in exc.value.asdict()['user']


def test_ResetPasswordSchema_with_expired_token(config, user_model):
    request = csrf_request(config)
    request.registry.password_reset_serializer = FakeExpiredSerializer()
    schema = schemas.ResetPasswordSchema().bind(request=request)

    with pytest.raises(colander.Invalid) as exc:
        schema.deserialize({
            'user': 'abc123',
            'password': 'secret',
        })

    assert 'user' in exc.value.asdict()
    assert 'reset code has expired' in exc.value.asdict()['user']


@pytest.mark.usefixtures('user_model')
def test_ResetPasswordSchema_user_has_already_reset_their_password(config,
                                                                   user_model):
    request = csrf_request(config)
    request.registry.password_reset_serializer = FakeSerializer()
    schema = schemas.ResetPasswordSchema().bind(request=request)
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
def test_ResetPasswordSchema_adds_user_to_appstruct(config, user_model):
    request = csrf_request(config)
    request.registry.password_reset_serializer = FakeSerializer()
    schema = schemas.ResetPasswordSchema().bind(request=request)
    user = user_model.get_by_username.return_value
    user.password_updated = 0

    appstruct = schema.deserialize({
        'user': 'abc123',
        'password': 'secret',
    })

    assert appstruct['user'] == user


def test_EmailChangeSchema_rejects_non_matching_emails(config, user_model):
    user = Mock()
    request = csrf_request(config, authenticated_user=user)
    schema = schemas.EmailChangeSchema().bind(request=request)
    # The email isn't taken
    user_model.get_by_email.return_value = None

    with pytest.raises(colander.Invalid) as exc:
        schema.deserialize({'email': 'foo@bar.com',
                            'email_confirm': 'foo@baz.com',
                            'password': 'flibble'})

    assert 'email_confirm' in exc.value.asdict()


def test_EmailChangeSchema_rejects_wrong_password(config, user_model):
    user = Mock()
    request = csrf_request(config, authenticated_user=user)
    schema = schemas.EmailChangeSchema().bind(request=request)
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


def test_PasswordChangeSchema_rejects_non_matching_passwords(config,
                                                             user_model):
    user = Mock()
    request = csrf_request(config, authenticated_user=user)
    schema = schemas.PasswordChangeSchema().bind(request=request)

    with pytest.raises(colander.Invalid) as exc:
        schema.deserialize({'new_password': 'wibble',
                            'new_password_confirm': 'wibble!',
                            'password': 'flibble'})

    assert 'new_password_confirm' in exc.value.asdict()


def test_PasswordChangeSchema_rejects_wrong_password(config, user_model):
    user = Mock()
    request = csrf_request(config, authenticated_user=user)
    schema = schemas.PasswordChangeSchema().bind(request=request)
    # The password does not check out
    user_model.validate_user.return_value = False

    with pytest.raises(colander.Invalid) as exc:
        schema.deserialize({'new_password': 'wibble',
                            'new_password_confirm': 'wibble!',
                            'password': 'flibble'})

    user_model.validate_user.assert_called_once_with(user, 'flibble')
    assert 'password' in exc.value.asdict()


@pytest.fixture
def activation_model(config, request):
    patcher = patch('h.accounts.schemas.models.Activation', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()


@pytest.fixture
def user_model(config, request):
    patcher = patch('h.accounts.schemas.models.User', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()
