# -*- coding: utf-8 -*-
import colander
import deform
import pytest
from mock import PropertyMock, patch
from pyramid.exceptions import BadCSRFToken
from pyramid.testing import DummyRequest

from h.accounts import models, schemas

valid_username = 'test'
valid_email = 'raven@poe.net'
valid_password = 'shhh'
valid_user = {'username': valid_username,
              'email': valid_email,
              'password': valid_password}


def csrf_request(config):
    request = DummyRequest(registry=config.registry)
    request.headers['X-CSRF-Token'] = request.session.get_csrf_token()
    return request


@pytest.yield_fixture(autouse=True)
def mock_user_ctor():
    def get_by_username(request, username):
        if username == valid_user['username']:
            return models.User(**valid_user)
            return None

    def get_by_email(request, email):
        if email == valid_user['email']:
            return models.User(**valid_user)
            return None

    def validate_user(user, password):
        return password == valid_user['password']

    is_activated = PropertyMock(return_value=False)
    with patch('h.accounts.models.User', autospec=True) as MockUser:
        MockUser.get_by_username.side_effect = get_by_username
        MockUser.get_by_email.side_effect = get_by_email
        MockUser.validate_user.side_effect = validate_user
        type(MockUser.return_value).is_activated = is_activated
        yield MockUser


def test_unblacklisted_username(config):
    config.include(models)

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


def test_login_bad_csrf(config):
    request = DummyRequest(registry=config.registry)
    schema = schemas.LoginSchema().bind(request=request)
    with pytest.raises(BadCSRFToken):
        schema.deserialize(valid_user)


def test_login_bad_username(config):
    config.include(models)
    request = csrf_request(config)
    schema = schemas.LoginSchema().bind(request=request)
    with pytest.raises(colander.Invalid) as exc:
        schema.deserialize({'username': 'bogus', 'password': 'foo'})
    assert 'username' in exc.value.asdict()


def test_login_bad_password(config):
    config.include(models)
    request = csrf_request(config)
    schema = schemas.LoginSchema().bind(request=request)
    with pytest.raises(colander.Invalid) as exc:
        schema.deserialize({
            'username': valid_username,
            'password': 'bogus',
        })
    assert 'password' in exc.value.asdict()


def test_login_good(config):
    config.registry.settings.update({'horus.require_activation': False})
    config.include(models)
    request = csrf_request(config)
    schema = schemas.LoginSchema().bind(request=request)
    assert 'user' in schema.deserialize({
        'username': valid_username,
        'password': valid_password,
    })


def test_login_email(config):
    config.registry.settings.update({
        'horus.require_activation': False,
    })
    config.include(models)
    request = csrf_request(config)
    schema = schemas.LoginSchema().bind(request=request)
    assert 'user' in schema.deserialize({
        'username': valid_email,
        'password': valid_password,
    })


def test_login_inactive(config):
    config.registry.settings.update({
        'horus.allow_inactive_login': False,
        'horus.require_activation': True,
    })
    config.include(models)
    request = csrf_request(config)
    schema = schemas.LoginSchema().bind(request=request)
    with pytest.raises(colander.Invalid) as exc:
        schema.deserialize(valid_user)
    assert 'not active' in exc.value.msg
