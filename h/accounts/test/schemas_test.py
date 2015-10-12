# -*- coding: utf-8 -*-
import colander
import deform
import pytest
from mock import patch
from pyramid.exceptions import BadCSRFToken
from pyramid.testing import DummyRequest

from h.accounts import schemas


class DummyNode(object):
    pass


def csrf_request(config):
    request = DummyRequest(registry=config.registry)
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

    try:
        schemas.unique_email(node, "foo@bar.com")
    except:
        pass

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

    result = schemas.unique_email(node, "foo@bar.com")

    assert result is None


def test_matching_emails_with_mismatched_emails():
    form = deform.Form(schemas.ProfileSchema())
    value = {
        "email": "foo",
        "emailAgain": "bar"
    }
    with pytest.raises(colander.Invalid):
        schemas.matching_emails(form, value)


def test_matching_emails_with_matched_emails():
    form = deform.Form(schemas.ProfileSchema())
    value = {
        "email": "foo",
        "emailAgain": "foo"
    }
    assert schemas.matching_emails(form, value) is None


def test_ProfileSchema_with_email_too_long(user_model):
    email = "bob@b" + "o" * 100 + "b.com"
    data = {"email": email, "emailAgain": email}
    schema = schemas.ProfileSchema().bind(request=DummyRequest())

    with pytest.raises(colander.Invalid) as err:
        schema.deserialize(data)
    assert 'email' in err.value.asdict()


def test_ProfileSchema_with_password_too_short(user_model):
    schema = schemas.ProfileSchema().bind(request=DummyRequest())

    with pytest.raises(colander.Invalid) as err:
        schema.deserialize({"password": "a"})
    assert "password" in err.value.asdict()


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


def test_login_bad_csrf(config, user_model):
    request = DummyRequest()
    schema = schemas.LoginSchema().bind(request=request)
    user = user_model.get_by_username.return_value
    user.is_activated = True

    with pytest.raises(BadCSRFToken):
        schema.deserialize({
            'username': 'jeannie',
            'password': 'cake',
        })


def test_login_bad_username(config, user_model):
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


def test_login_bad_password(config, user_model):
    request = csrf_request(config)
    schema = schemas.LoginSchema().bind(request=request)
    user_model.validate_user.return_value = False

    with pytest.raises(colander.Invalid) as exc:
        schema.deserialize({
            'username': 'jeannie',
            'password': 'cake',
        })

    assert 'password' in exc.value.asdict()


def test_login_good(config, user_model):
    request = csrf_request(config)
    user = user_model.get_by_username.return_value
    user.is_activated = True

    schema = schemas.LoginSchema().bind(request=request)

    assert 'user' in schema.deserialize({
        'username': 'jeannie',
        'password': 'cake',
    })


def test_login_email(config, user_model):
    request = csrf_request(config)
    schema = schemas.LoginSchema().bind(request=request)
    user_model.get_by_username.return_value = None
    user = user_model.get_by_email.return_value
    user.is_activated = True

    assert 'user' in schema.deserialize({
        'username': 'jeannie',
        'password': 'cake',
    })


def test_login_inactive(config, user_model):
    request = csrf_request(config)
    user = user_model.get_by_username.return_value
    user.is_activated = False
    schema = schemas.LoginSchema().bind(request=request)

    with pytest.raises(colander.Invalid) as exc:
        schema.deserialize({
            'username': 'jeannie',
            'password': 'cake',
        })

    assert 'not active' in exc.value.msg


def test_forgot_password_invalid_with_no_user(config, user_model):
    request = csrf_request(config)
    schema = schemas.ForgotPasswordSchema().bind(request=request)
    user_model.get_by_email.return_value = None

    with pytest.raises(colander.Invalid) as exc:
        schema.deserialize({'email': 'rapha@example.com'})

    assert 'email' in exc.value.asdict()
    assert 'no user with the email address' in exc.value.asdict()['email']


def test_forgot_password_adds_user_to_appstruct(config, user_model):
    request = csrf_request(config)
    schema = schemas.ForgotPasswordSchema().bind(request=request)
    user = user_model.get_by_email.return_value

    appstruct = schema.deserialize({'email': 'rapha@example.com'})

    assert appstruct['user'] == user


@pytest.mark.usefixtures('user_model')
def test_reset_password_no_activation(config, activation_model):
    request = csrf_request(config)
    schema = schemas.ResetPasswordSchema().bind(request=request)
    activation_model.get_by_code.return_value = None

    with pytest.raises(colander.Invalid) as exc:
        schema.deserialize({
            'user': 'abc123',
            'password': 'secret',
        })

    assert 'user' in exc.value.asdict()
    assert 'reset code is not valid' in exc.value.asdict()['user']


@pytest.mark.usefixtures('activation_model')
def test_reset_password_no_user_for_activation(config, user_model):
    request = csrf_request(config)
    schema = schemas.ResetPasswordSchema().bind(request=request)
    user_model.get_by_activation.return_value = None

    with pytest.raises(colander.Invalid) as exc:
        schema.deserialize({
            'user': 'abc123',
            'password': 'secret',
        })

    assert 'user' in exc.value.asdict()
    assert 'reset code is not valid' in exc.value.asdict()['user']


def test_reset_password_adds_user_to_appstruct(config,
                                               activation_model,
                                               user_model):
    request = csrf_request(config)
    schema = schemas.ResetPasswordSchema().bind(request=request)
    user = user_model.get_by_activation.return_value

    appstruct = schema.deserialize({
        'user': 'abc123',
        'password': 'secret',
    })

    assert appstruct['user'] == user


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
