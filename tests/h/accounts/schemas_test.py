# -*- coding: utf-8 -*-
import colander
import pytest
from mock import Mock
from pyramid.exceptions import BadCSRFToken
from itsdangerous import BadData, SignatureExpired

from h.accounts import schemas


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
                                                   "foo@bar.com")

    def test_it_is_invalid_when_user_exists(self, dummy_node):
        pytest.raises(colander.Invalid,
                      schemas.unique_email,
                      dummy_node,
                      "foo@bar.com")

    def test_it_is_invalid_when_user_does_not_exist(self,
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
            "Shorter than minimum length 2")

    def test_it_is_invalid_when_username_too_short(self,
                                                   pyramid_request,
                                                   user_model):
        schema = schemas.RegisterSchema().bind(request=pyramid_request)
        user_model.get_by_username.return_value = None

        with pytest.raises(colander.Invalid) as exc:
            schema.deserialize({"username": "a"})
        assert exc.value.asdict()['username'] == (
            "Shorter than minimum length 3")

    def test_it_is_invalid_when_username_too_long(self,
                                                  pyramid_request,
                                                  user_model):
        schema = schemas.RegisterSchema().bind(request=pyramid_request)
        user_model.get_by_username.return_value = None

        with pytest.raises(colander.Invalid) as exc:
            schema.deserialize({"username": "a" * 500})
        assert exc.value.asdict()['username'] == (
            "Longer than maximum length 30")

    def test_it_is_invalid_with_invalid_characters_in_username(self,
                                                               pyramid_request,
                                                               user_model):
        user_model.get_by_username.return_value = None
        schema = schemas.RegisterSchema().bind(request=pyramid_request)

        with pytest.raises(colander.Invalid) as exc:
            schema.deserialize({"username": "Fred Flintstone"})
        assert exc.value.asdict()['username'] == ("Must contain only letters, "
                                                  "numbers, periods, and "
                                                  "underscores")


@pytest.mark.usefixtures('user_model')
class TestLoginSchema(object):

    def test_it_is_invalid_with_bad_csrf(self, pyramid_request, user_model):
        schema = schemas.LoginSchema().bind(request=pyramid_request)
        user = user_model.get_by_username.return_value
        user.is_activated = True

        with pytest.raises(BadCSRFToken):
            schema.deserialize({
                'username': 'jeannie',
                'password': 'cake',
            })

    def test_it_is_invalid_with_bad_username(self,
                                             pyramid_csrf_request,
                                             user_model):
        schema = schemas.LoginSchema().bind(request=pyramid_csrf_request)
        user_model.get_by_username.return_value = None
        user_model.get_by_email.return_value = None

        with pytest.raises(colander.Invalid) as exc:
            schema.deserialize({
                'username': 'jeannie',
                'password': 'cake',
            })

        assert 'username' in exc.value.asdict()

    def test_it_is_invalid_with_bad_password(self,
                                             pyramid_csrf_request,
                                             user_model):
        schema = schemas.LoginSchema().bind(request=pyramid_csrf_request)
        user = user_model.get_by_username.return_value
        user.check_password.return_value = False

        with pytest.raises(colander.Invalid) as exc:
            schema.deserialize({
                'username': 'jeannie',
                'password': 'cake',
            })

        assert 'password' in exc.value.asdict()

    def test_it_returns_user_when_valid(self,
                                        pyramid_csrf_request,
                                        user_model):
        user = user_model.get_by_username.return_value
        user.is_activated = True

        schema = schemas.LoginSchema().bind(request=pyramid_csrf_request)

        assert 'user' in schema.deserialize({
            'username': 'jeannie',
            'password': 'cake',
        })

    def test_it_is_valid_with_email_instead_of_username(self,
                                                        pyramid_csrf_request,
                                                        user_model):
        """If get_by_username() returns None it should try get_by_email()."""
        schema = schemas.LoginSchema().bind(request=pyramid_csrf_request)
        user_model.get_by_username.return_value = None
        user = user_model.get_by_email.return_value
        user.is_activated = True

        assert 'user' in schema.deserialize({
            'username': 'jeannie',
            'password': 'cake',
        })

    def test_it_is_invalid_with_inactive_user_account(self,
                                                      pyramid_csrf_request,
                                                      user_model):
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


@pytest.mark.usefixtures('user_model')
class TestForgotPasswordSchema(object):

    def test_it_is_invalid_with_no_user(self,
                                        pyramid_csrf_request,
                                        user_model):
        schema = schemas.ForgotPasswordSchema().bind(
            request=pyramid_csrf_request)
        user_model.get_by_email.return_value = None

        with pytest.raises(colander.Invalid) as exc:
            schema.deserialize({'email': 'rapha@example.com'})

        assert 'email' in exc.value.asdict()
        assert exc.value.asdict()['email'] == 'Unknown email address'

    def test_it_returns_user_when_valid(self,
                                        pyramid_csrf_request,
                                        user_model):
        schema = schemas.ForgotPasswordSchema().bind(
            request=pyramid_csrf_request)
        user = user_model.get_by_email.return_value

        appstruct = schema.deserialize({'email': 'rapha@example.com'})

        assert appstruct['user'] == user


@pytest.mark.usefixtures('user_model')
class TestResetPasswordSchema(object):

    def test_it_is_invalid_with_password_too_short(self, pyramid_csrf_request):
        schema = schemas.ResetPasswordSchema().bind(
            request=pyramid_csrf_request)

        with pytest.raises(colander.Invalid) as exc:
            schema.deserialize({"password": "a"})
        assert "password" in exc.value.asdict()

    def test_it_is_invalid_with_invalid_user_token(self, pyramid_csrf_request):
        pyramid_csrf_request.registry.password_reset_serializer = (
            self.FakeInvalidSerializer())
        schema = schemas.ResetPasswordSchema().bind(
            request=pyramid_csrf_request)

        with pytest.raises(colander.Invalid) as exc:
            schema.deserialize({
                'user': 'abc123',
                'password': 'secret',
            })

        assert 'user' in exc.value.asdict()
        assert 'reset code is not valid' in exc.value.asdict()['user']

    def test_it_is_invalid_with_expired_token(self, pyramid_csrf_request):
        pyramid_csrf_request.registry.password_reset_serializer = (
            self.FakeExpiredSerializer())
        schema = schemas.ResetPasswordSchema().bind(
            request=pyramid_csrf_request)

        with pytest.raises(colander.Invalid) as exc:
            schema.deserialize({
                'user': 'abc123',
                'password': 'secret',
            })

        assert 'user' in exc.value.asdict()
        assert 'reset code has expired' in exc.value.asdict()['user']

    def test_it_is_invalid_if_user_has_already_reset_their_password(
            self, pyramid_csrf_request, user_model):
        pyramid_csrf_request.registry.password_reset_serializer = (
            self.FakeSerializer())
        schema = schemas.ResetPasswordSchema().bind(
            request=pyramid_csrf_request)
        user = user_model.get_by_username.return_value
        user.password_updated = 2

        with pytest.raises(colander.Invalid) as exc:
            schema.deserialize({
                'user': 'abc123',
                'password': 'secret',
            })

        assert 'user' in exc.value.asdict()
        assert 'already reset your password' in exc.value.asdict()['user']

    def test_it_returns_user_when_valid(self,
                                        pyramid_csrf_request,
                                        user_model):
        pyramid_csrf_request.registry.password_reset_serializer = (
            self.FakeSerializer())
        schema = schemas.ResetPasswordSchema().bind(
            request=pyramid_csrf_request)
        user = user_model.get_by_username.return_value
        user.password_updated = 0

        appstruct = schema.deserialize({
            'user': 'abc123',
            'password': 'secret',
        })

        assert appstruct['user'] == user

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


@pytest.mark.usefixtures('user_model')
class TestLegacyEmailChangeSchema(object):

    def test_it_is_invalid_if_emails_dont_match(self,
                                                pyramid_csrf_request,
                                                user_model):
        user = Mock()
        pyramid_csrf_request.authenticated_user = user
        schema = schemas.LegacyEmailChangeSchema().bind(
            request=pyramid_csrf_request)
        # The email isn't taken
        user_model.get_by_email.return_value = None

        with pytest.raises(colander.Invalid) as exc:
            schema.deserialize({'email': 'foo@bar.com',
                                'email_confirm': 'foo@baz.com',
                                'password': 'flibble'})

        assert 'email_confirm' in exc.value.asdict()

    def test_it_is_invalid_if_password_wrong(self,
                                             pyramid_csrf_request,
                                             user_model):
        user = Mock()
        pyramid_csrf_request.authenticated_user = user
        schema = schemas.LegacyEmailChangeSchema().bind(
            request=pyramid_csrf_request)
        # The email isn't taken
        user_model.get_by_email.return_value = None
        # The password does not check out
        user.check_password.return_value = False

        with pytest.raises(colander.Invalid) as exc:
            schema.deserialize({'email': 'foo@bar.com',
                                'email_confirm': 'foo@bar.com',
                                'password': 'flibble'})

        user.check_password.assert_called_once_with('flibble')
        assert 'password' in exc.value.asdict()


@pytest.mark.usefixtures('user_model')
class TestEmailChangeSchema(object):

    def test_it_is_invalid_if_password_wrong(self,
                                             db_session,
                                             factories,
                                             pyramid_csrf_request):
        pyramid_csrf_request.authenticated_user = factories.User()
        db_session.add(pyramid_csrf_request.authenticated_user)
        schema = schemas.EmailChangeSchema().bind(request=pyramid_csrf_request)

        with pytest.raises(colander.Invalid) as exc:
            schema.deserialize({
                'email': 'foo@bar.com',
                'password': 'flibble'  # Not the correct password!
            })

        assert 'password' in exc.value.asdict()


class TestPasswordChangeSchema(object):

    def test_it_is_invalid_if_passwords_dont_match(self, pyramid_csrf_request):
        user = Mock()
        pyramid_csrf_request.authenticated_user = user
        schema = schemas.PasswordChangeSchema().bind(
            request=pyramid_csrf_request)

        with pytest.raises(colander.Invalid) as exc:
            schema.deserialize({'new_password': 'wibble',
                                'new_password_confirm': 'wibble!',
                                'password': 'flibble'})

        assert 'new_password_confirm' in exc.value.asdict()

    def test_it_is_invalid_if_current_password_is_wrong(self,
                                                        pyramid_csrf_request):
        user = Mock()
        pyramid_csrf_request.authenticated_user = user
        schema = schemas.PasswordChangeSchema().bind(
            request=pyramid_csrf_request)
        # The password does not check out
        user.check_password.return_value = False

        with pytest.raises(colander.Invalid) as exc:
            schema.deserialize({'new_password': 'wibble',
                                'new_password_confirm': 'wibble',
                                'password': 'flibble'})

        user.check_password.assert_called_once_with('flibble')
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
