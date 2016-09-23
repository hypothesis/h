# -*- coding: utf-8 -*-
import colander
import pytest
from mock import Mock
from pyramid.exceptions import BadCSRFToken
from itsdangerous import BadData, SignatureExpired

from h.accounts import schemas
from h.accounts.services import UserNotActivated, UserNotKnown, UserService


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


@pytest.mark.usefixtures('user_service')
class TestLoginSchema(object):

    def test_passes_username_and_password_to_user_service(self,
                                                          factories,
                                                          pyramid_csrf_request,
                                                          user_service):
        user = factories.User(username='jeannie')
        user_service.login.return_value = user
        schema = schemas.LoginSchema().bind(request=pyramid_csrf_request)

        schema.deserialize({
            'username': 'jeannie',
            'password': 'cake',
        })

        user_service.login.assert_called_once_with(username_or_email='jeannie',
                                                   password='cake')

    def test_it_returns_user_when_valid(self,
                                        factories,
                                        pyramid_csrf_request,
                                        user_service):
        user = factories.User(username='jeannie')
        user_service.login.return_value = user
        schema = schemas.LoginSchema().bind(request=pyramid_csrf_request)

        result = schema.deserialize({
            'username': 'jeannie',
            'password': 'cake',
        })

        assert result['user'] is user

    def test_invalid_with_bad_csrf(self, pyramid_request, user_service):
        schema = schemas.LoginSchema().bind(request=pyramid_request)

        with pytest.raises(BadCSRFToken):
            schema.deserialize({
                'username': 'jeannie',
                'password': 'cake',
            })

    def test_invalid_with_inactive_user(self,
                                        pyramid_csrf_request,
                                        user_service):
        schema = schemas.LoginSchema().bind(request=pyramid_csrf_request)
        user_service.login.side_effect = UserNotActivated()

        with pytest.raises(colander.Invalid) as exc:
            schema.deserialize({
                'username': 'jeannie',
                'password': 'cake',
            })
        errors = exc.value.asdict()

        assert 'username' in errors
        assert 'activate your account' in errors['username']

    def test_invalid_with_unknown_user(self,
                                       pyramid_csrf_request,
                                       user_service):
        schema = schemas.LoginSchema().bind(request=pyramid_csrf_request)
        user_service.login.side_effect = UserNotKnown()

        with pytest.raises(colander.Invalid) as exc:
            schema.deserialize({
                'username': 'jeannie',
                'password': 'cake',
            })
        errors = exc.value.asdict()

        assert 'username' in errors
        assert 'does not exist' in errors['username']


    def test_invalid_with_bad_password(self,
                                       pyramid_csrf_request,
                                       user_service):
        user_service.login.return_value = None
        schema = schemas.LoginSchema().bind(request=pyramid_csrf_request)

        with pytest.raises(colander.Invalid) as exc:
            schema.deserialize({
                'username': 'jeannie',
                'password': 'cake',
            })
        errors = exc.value.asdict()

        assert 'password' in errors
        assert 'Wrong password' in errors['password']


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
        assert exc.value.asdict()['email'] == 'Unknown email address.'

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
        assert 'Wrong reset code.' in exc.value.asdict()['user']

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
        assert 'Reset code has expired.' in exc.value.asdict()['user']

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
        assert 'This reset code has already been used.' in exc.value.asdict()['user']

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


@pytest.mark.usefixtures('models')
class TestEmailChangeSchema(object):

    # The user's password.
    PASSWORD = 'flibble'

    def test_it_returns_the_new_email_when_valid(self, schema):
        appstruct = schema.deserialize({
            'email': 'foo@bar.com',
            'password': self.PASSWORD,
        })

        assert appstruct['email'] == 'foo@bar.com'

    def test_it_is_valid_if_email_same_as_users_existing_email(self,
                                                               schema,
                                                               user,
                                                               models,
                                                               pyramid_config):
        """
        It is valid if the new email is the same as the user's existing one.

        Trying to change your email to what your email already is should not
        return an error.

        """
        models.User.get_by_email.return_value = Mock(spec_set=['userid'],
                                                      userid=user.userid)
        pyramid_config.testing_securitypolicy(user.userid)

        schema.deserialize({'email': user.email, 'password': self.PASSWORD})

    def test_it_is_invalid_if_csrf_token_missing(self,
                                                 pyramid_request,
                                                 schema):
        del pyramid_request.headers['X-CSRF-Token']

        with pytest.raises(BadCSRFToken):
            schema.deserialize({
                'email': 'foo@bar.com',
                'password': self.PASSWORD,
            })

    def test_it_is_invalid_if_csrf_token_wrong(self, pyramid_request, schema):
        pyramid_request.headers['X-CSRF-Token'] = 'WRONG'

        with pytest.raises(BadCSRFToken):
            schema.deserialize({
                'email': 'foo@bar.com',
                'password': self.PASSWORD,
            })

    def test_it_is_invalid_if_password_wrong(self, schema):
        with pytest.raises(colander.Invalid) as exc:
            schema.deserialize({
                'email': 'foo@bar.com',
                'password': 'WRONG'  # Not the correct password!
            })

        assert exc.value.asdict() == {'password': 'Wrong password.'}

    def test_it_returns_incorrect_password_error_if_password_too_short(
            self, schema):
        """
        The schema should be invalid if the password is too short.

        Test that this returns a "that was not the right password" error rather
        than a "that password is too short error" as it used to (the user is
        entering their current password for authentication, they aren't
        choosing a new password).

        """
        with pytest.raises(colander.Invalid) as exc:
            schema.deserialize({
                'email': 'foo@bar.com',
                'password': 'a'  # Too short to be a valid password.
            })

        assert exc.value.asdict() == {'password': 'Wrong password.'}

    def test_it_is_invalid_if_email_too_long(self, schema):
        with pytest.raises(colander.Invalid) as exc:
            schema.deserialize({
                'email': 'a' * 100 + '@bar.com',
                'password': self.PASSWORD,
            })

        assert exc.value.asdict() == {
            'email': 'Must be 100 characters or less.'}

    def test_it_is_invalid_if_email_not_a_valid_email_address(self, schema):
        with pytest.raises(colander.Invalid) as exc:
            schema.deserialize({
                'email': 'this is not a valid email address',
                'password': self.PASSWORD,
            })

        assert exc.value.asdict() == {'email': 'Invalid email address.'}

    def test_it_is_invalid_if_email_already_taken(self, models, schema):
        models.User.get_by_email.return_value = Mock(spec_set=['userid'])

        with pytest.raises(colander.Invalid) as exc:
            schema.deserialize({
                'email': 'foo@bar.com',
                'password': self.PASSWORD,
            })

        assert exc.value.asdict() == {'email': 'Sorry, an account with this '
                                               'email address already exists.'}

    @pytest.fixture
    def pyramid_request(self, pyramid_csrf_request, user):
        pyramid_csrf_request.authenticated_user = user
        return pyramid_csrf_request

    @pytest.fixture
    def schema(self, pyramid_request):
        return schemas.EmailChangeSchema().bind(request=pyramid_request)

    @pytest.fixture
    def user(self, factories):
        return factories.User(password=self.PASSWORD)

    @pytest.fixture
    def models(self, patch):
        models = patch('h.accounts.schemas.models')

        # By default there isn't already an account with the email address that
        # we're trying to change to.
        models.User.get_by_email.return_value = None

        return models


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


class TestEditProfileSchema(object):
    def test_accepts_valid_input(self, pyramid_csrf_request):
        schema = schemas.EditProfileSchema().bind(request=pyramid_csrf_request)
        appstruct = schema.deserialize({
            'display_name': 'Michael Granitzer',
            'description': 'Professor at University of Passau',
            'link': 'http://mgrani.github.io/',
            'location': 'Bavaria, Germany',
            'orcid': '0000-0003-3566-5507',
        })

    def test_rejects_invalid_orcid(self, pyramid_csrf_request, validate_orcid):
        validate_orcid.side_effect = ValueError('Invalid ORCID')
        schema = schemas.EditProfileSchema().bind(request=pyramid_csrf_request)
        with pytest.raises(colander.Invalid) as exc:
            schema.deserialize({'orcid': 'abcdef'})
        assert exc.value.asdict()['orcid'] == 'Invalid ORCID'

    def test_rejects_invalid_url(self, pyramid_csrf_request, validate_url):
        validate_url.side_effect = ValueError('Invalid URL')
        schema = schemas.EditProfileSchema().bind(request=pyramid_csrf_request)
        with pytest.raises(colander.Invalid) as exc:
            schema.deserialize({'link': '"invalid URL"'})
        assert exc.value.asdict()['link'] == 'Invalid URL'


@pytest.fixture
def validate_url(patch):
    return patch('h.accounts.schemas.util.validate_url')


@pytest.fixture
def validate_orcid(patch):
    return patch('h.accounts.schemas.util.validate_orcid')


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
    service.login.return_value = None
    pyramid_config.register_service(service, name='user')
    return service
