# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import colander
import pytest
from mock import Mock

from h.accounts import schemas
from h.services.user import UserService
from h.services.user_password import UserPasswordService


class TestUnblacklistedUsername(object):

    def test(self, dummy_node):
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


@pytest.mark.usefixtures('user_model')
class TestUniqueEmail(object):

    def test_it_looks_up_user_by_email(self,
                                       dummy_node,
                                       pyramid_request,
                                       user_model):
        with pytest.raises(colander.Invalid):
            schemas.unique_email(dummy_node, "foo@bar.com")

        user_model.get_by_email.assert_called_with(pyramid_request.db,
                                                   "foo@bar.com",
                                                   pyramid_request.default_authority)

    def test_it_is_invalid_when_user_exists(self, dummy_node):
        pytest.raises(colander.Invalid,
                      schemas.unique_email,
                      dummy_node,
                      "foo@bar.com")

    def test_it_is_valid_when_user_does_not_exist(self,
                                                  dummy_node,
                                                  user_model):
        user_model.get_by_email.return_value = None

        assert schemas.unique_email(dummy_node, "foo@bar.com") is None

    def test_it_is_valid_when_authorized_users_email(self,
                                                     dummy_node,
                                                     pyramid_config,
                                                     user_model):
        """
        If the given email is the authorized user's current email it's valid.

        This is so that we don't get a "That email is already taken" validation
        error when a user tries to change their email address to the same email
        address that they already have it set to.

        """
        pyramid_config.testing_securitypolicy('acct:elliot@hypothes.is')
        user_model.get_by_email.return_value = Mock(
            spec_set=('userid',),
            userid='acct:elliot@hypothes.is')

        schemas.unique_email(dummy_node, "elliot@bar.com")


@pytest.mark.usefixtures('user_model')
class TestRegisterSchema(object):

    def test_it_is_invalid_when_password_too_short(self, pyramid_request):
        schema = schemas.RegisterSchema().bind(request=pyramid_request)

        with pytest.raises(colander.Invalid) as exc:
            schema.deserialize({"password": "a"})
        assert exc.value.asdict()['password'] == (
            "Must be 2 characters or more.")

    def test_it_is_invalid_when_username_too_short(self,
                                                   pyramid_request,
                                                   user_model):
        schema = schemas.RegisterSchema().bind(request=pyramid_request)
        user_model.get_by_username.return_value = None

        with pytest.raises(colander.Invalid) as exc:
            schema.deserialize({"username": "a"})
        assert exc.value.asdict()['username'] == (
            "Must be 3 characters or more.")

    def test_it_is_invalid_when_username_too_long(self,
                                                  pyramid_request,
                                                  user_model):
        schema = schemas.RegisterSchema().bind(request=pyramid_request)
        user_model.get_by_username.return_value = None

        with pytest.raises(colander.Invalid) as exc:
            schema.deserialize({"username": "a" * 500})
        assert exc.value.asdict()['username'] == (
            "Must be 30 characters or less.")

    def test_it_is_invalid_with_invalid_characters_in_username(self,
                                                               pyramid_request,
                                                               user_model):
        user_model.get_by_username.return_value = None
        schema = schemas.RegisterSchema().bind(request=pyramid_request)

        with pytest.raises(colander.Invalid) as exc:
            schema.deserialize({"username": "Fred Flintstone"})
        assert exc.value.asdict()['username'] == ("Must have only letters, "
                                                  "numbers, periods, and "
                                                  "underscores.")

    def test_it_is_invalid_with_false_privacy_accepted(self, pyramid_request):
        schema = schemas.RegisterSchema().bind(request=pyramid_request)

        with pytest.raises(colander.Invalid) as exc:
            schema.deserialize({"privacy_accepted": 'false'})

        assert exc.value.asdict()['privacy_accepted'] == "Acceptance of the privacy policy is required"

    def test_it_is_invalid_when_privacy_accepted_missing(self,
                                                         pyramid_request):
        schema = schemas.RegisterSchema().bind(request=pyramid_request)

        with pytest.raises(colander.Invalid) as exc:
            schema.deserialize({})

        assert exc.value.asdict()['privacy_accepted'] == "Required"

    def test_it_validates_with_valid_payload(self, pyramid_csrf_request, user_model):
        user_model.get_by_username.return_value = None
        user_model.get_by_email.return_value = None

        schema = schemas.RegisterSchema().bind(request=pyramid_csrf_request)
        schema.deserialize({
            "username": "filbert",
            "email": "foo@bar.com",
            "password": "sdlkfjlk3j3iuei",
            "privacy_accepted": "true",
        })


@pytest.mark.usefixtures('user_password_service')
class TestPasswordChangeSchema(object):

    def test_it_is_invalid_if_passwords_dont_match(self, pyramid_csrf_request):
        user = Mock()
        pyramid_csrf_request.user = user
        schema = schemas.PasswordChangeSchema().bind(
            request=pyramid_csrf_request)

        with pytest.raises(colander.Invalid) as exc:
            schema.deserialize({'new_password': 'wibble',
                                'new_password_confirm': 'wibble!',
                                'password': 'flibble'})

        assert 'new_password_confirm' in exc.value.asdict()

    def test_it_is_invalid_if_current_password_is_wrong(self,
                                                        pyramid_csrf_request,
                                                        user_password_service):
        user = Mock()
        pyramid_csrf_request.user = user
        schema = schemas.PasswordChangeSchema().bind(
            request=pyramid_csrf_request)
        user_password_service.check_password.return_value = False

        with pytest.raises(colander.Invalid) as exc:
            schema.deserialize({'new_password': 'wibble',
                                'new_password_confirm': 'wibble',
                                'password': 'flibble'})

        user_password_service.check_password.assert_called_once_with(user, 'flibble')
        assert 'password' in exc.value.asdict()


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


@pytest.fixture
def user_service(db_session, pyramid_config):
    service = Mock(spec_set=UserService(default_authority='example.com',
                                        session=db_session))
    service.fetch_for_login.return_value = None
    pyramid_config.register_service(service, name='user')
    return service


@pytest.fixture
def user_password_service(pyramid_config):
    service = Mock(spec_set=UserPasswordService())
    service.check_password.return_value = True
    pyramid_config.register_service(service, name='user_password')
    return service
