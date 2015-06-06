# -*- coding: utf-8 -*-
import colander
import deform
import pytest
from mock import PropertyMock, patch
from pyramid.exceptions import BadCSRFToken
from pyramid.testing import DummyRequest

from h.accounts import models, schemas


def csrf_request(config):
    request = DummyRequest(registry=config.registry)
    request.headers['X-CSRF-Token'] = request.session.get_csrf_token()
    return request


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
    config.include(models)
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


@pytest.fixture
def user_model(config, request):
    patcher = patch('h.accounts.schemas.User', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()
