import datetime
from unittest.mock import call, create_autospec, sentinel

import pytest

from h.models import Activation, User
from h.services.user_signup import (
    EmailConflictError,
    IdentityConflictError,
    UsernameConflictError,
    UserSignupService,
    user_signup_service_factory,
)
from h.tasks import email


class TestUserSignupService:
    def test_signup_returns_user(self, svc):
        user = svc.signup(username="foo", email="foo@bar.com")

        assert isinstance(user, User)

    def test_signup_creates_user_in_db(self, db_session, svc):
        svc.signup(username="foo", email="foo@bar.com")

        db_session.commit()
        db_session.close()

        user = db_session.query(User).filter_by(username="foo").one_or_none()
        assert user is not None

    def test_signup_creates_activation_for_user(self, svc):
        user = svc.signup(username="foo", email="foo@bar.com")

        assert isinstance(user.activation, Activation)

    def test_signup_does_not_create_activation_for_user_when_activation_not_required(
        self, svc
    ):
        user = svc.signup(require_activation=False, username="foo", email="foo@bar.com")

        assert user.activation is None

    def test_signup_sets_default_authority(self, svc):
        user = svc.signup(username="foo", email="foo@bar.com")

        assert user.authority == "example.org"

    def test_signup_allows_authority_override(self, svc):
        user = svc.signup(
            username="foo", email="foo@bar.com", authority="bar-client.com"
        )

        assert user.authority == "bar-client.com"

    def test_signup_allows_user_with_empty_identities(self, svc):
        user = svc.signup(require_activation=False, username="foo", identities=[])

        assert user.identities == []

    def test_signup_passes_through_privacy_acceptance(self, svc):
        now = datetime.datetime.utcnow()  # noqa: DTZ003
        user = svc.signup(username="foo", email="foo@bar.com", privacy_accepted=now)

        assert user.privacy_accepted == now

    def test_signup_passes_through_comms_opt_in(self, svc):
        user = svc.signup(username="foo", email="foo@bar.com", comms_opt_in=True)

        assert user.comms_opt_in

    def test_signup_sets_provided_user_identities(self, svc):
        identity_data = [
            {"provider": "someprovider", "provider_unique_id": 1},
            {"provider": "someotherprovider", "provider_unique_id": "394ffa3"},
        ]

        user = svc.signup(username="foo", email="foo@bar.com", identities=identity_data)

        assert len(user.identities) == 2

    def test_signup_sets_password_using_password_service(
        self, svc, user_password_service
    ):
        user = svc.signup(username="foo", email="foo@bar.com", password="wibble")  # noqa: S106

        user_password_service.update_password.assert_called_once_with(user, "wibble")

    def test_signup_sends_email(
        self, svc, signup, tasks_email, pyramid_request, asdict, TaskData
    ):
        signup.generate.return_value = sentinel.email_data

        user = svc.signup(username="foo", email="foo@bar.com")

        signup.generate.assert_called_once_with(
            request=pyramid_request,
            user_id=user.id,
            email="foo@bar.com",
            activation_code=user.activation.code,
        )

        asdict.assert_has_calls(
            [call(signup.generate.return_value), call(TaskData.return_value)]
        )
        tasks_email.send.delay.assert_called_once_with(
            sentinel.email_data, sentinel.task_data
        )

    def test_signup_does_not_send_email_when_activation_not_required(
        self, svc, signup, tasks_email
    ):
        svc.signup(require_activation=False, username="foo", email="foo@bar.com")

        signup.generate.assert_not_called()
        tasks_email.send.delay.assert_not_called()

    def test_signup_creates_subscriptions(self, svc, subscription_service, factories):
        subscription = factories.Subscriptions(active=False)
        subscription_service.get_all_subscriptions.return_value = [subscription]
        user = svc.signup(username="foo", email="foo@bar.com")

        subscription_service.get_all_subscriptions.assert_called_once_with(
            user_id=user.userid
        )
        assert subscription.active

    @pytest.mark.parametrize(
        "first_account,second_account,exception_class",
        [
            pytest.param(
                {"username": "foo"},
                {"username": "foo"},
                UsernameConflictError,
                id="conflicting_username",
            ),
            pytest.param(
                {"username": "foo", "email": "foo@foo.com"},
                {"username": "bar", "email": "foo@foo.com"},
                EmailConflictError,
                id="conflicting_email",
            ),
            pytest.param(
                {"username": "foo", "email": "foo@foo.com"},
                {"username": "foo", "email": "foo@foo.com"},
                # If both the username and the email address conflict the DB
                # seems to complain about the email address only.
                EmailConflictError,
                id="conflicting_username_and_email",
            ),
            pytest.param(
                {
                    "username": "foo",
                    "email": "foo@foo.com",
                    "identities": [
                        {
                            "provider": "google.com",
                            "provider_unique_id": "123",
                        }
                    ],
                },
                {
                    "username": "bar",
                    "email": "bar@bar.com",
                    "identities": [
                        {
                            "provider": "google.com",
                            "provider_unique_id": "123",
                        }
                    ],
                },
                IdentityConflictError,
                id="conflicting_identity",
            ),
            pytest.param(
                {
                    "username": "foo",
                    "email": "foo@foo.com",
                    "identities": [
                        {
                            "provider": "google.com",
                            "provider_unique_id": "123",
                        }
                    ],
                },
                {
                    "username": "foo",
                    "email": "foo2@foo.com",
                    "identities": [
                        {
                            "provider": "google.com",
                            "provider_unique_id": "123",
                        }
                    ],
                },
                # If both the username and the identity are in conflict the DB
                # seems to complain about the username only.
                UsernameConflictError,
                id="conflicting_username_and_identity",
            ),
            pytest.param(
                {
                    "username": "foo",
                    "email": "foo@foo.com",
                    "identities": [
                        {
                            "provider": "google.com",
                            "provider_unique_id": "123",
                        }
                    ],
                },
                {
                    "username": "bar",
                    "email": "foo@foo.com",
                    "identities": [
                        {
                            "provider": "google.com",
                            "provider_unique_id": "123",
                        }
                    ],
                },
                # If both the email and the identity are in conflict the DB
                # seems to complain about the email only.
                EmailConflictError,
                id="conflicting_email_and_identity",
            ),
            pytest.param(
                {
                    "username": "foo",
                    "email": "foo@foo.com",
                    "identities": [
                        {
                            "provider": "google.com",
                            "provider_unique_id": "123",
                        }
                    ],
                },
                {
                    "username": "foo",
                    "email": "foo@foo.com",
                    "identities": [
                        {
                            "provider": "google.com",
                            "provider_unique_id": "123",
                        }
                    ],
                },
                # If all three of the username, email and identity are in
                # conflict the DB seems to complain about the email only.
                EmailConflictError,
                id="conflicting_username_and_email_and_identity",
            ),
        ],
    )
    def test_signup_conflicts(
        self, svc, first_account, second_account, exception_class
    ):
        svc.signup(**first_account)

        with pytest.raises(exception_class):
            svc.signup(**second_account)

    @pytest.fixture
    def svc(self, pyramid_request, user_password_service, subscription_service):
        return UserSignupService(
            request=pyramid_request,
            default_authority="example.org",
            password_service=user_password_service,
            subscription_service=subscription_service,
        )

    @pytest.fixture(autouse=True)
    def tasks_email(self, patch):
        mock = patch("h.services.user_signup.email")
        mock.send.delay = create_autospec(email.send.run)
        return mock

    @pytest.fixture(autouse=True)
    def signup(self, patch):
        return patch("h.services.user_signup.signup")

    @pytest.fixture(autouse=True)
    def asdict(self, patch):
        return patch(
            "h.services.user_signup.asdict",
            side_effect=[sentinel.email_data, sentinel.task_data],
        )


@pytest.mark.usefixtures("user_password_service")
class TestUserSignupServiceFactory:
    def test_it(
        self,
        UserSignupService,
        pyramid_request,
        user_password_service,
        subscription_service,
    ):
        svc = user_signup_service_factory(sentinel.context, pyramid_request)

        UserSignupService.assert_called_once_with(
            request=pyramid_request,
            default_authority=pyramid_request.default_authority,
            password_service=user_password_service,
            subscription_service=subscription_service,
        )
        assert svc == UserSignupService.return_value

    @pytest.fixture
    def UserSignupService(self, patch):
        return patch("h.services.user_signup.UserSignupService")


@pytest.fixture(autouse=True)
def TaskData(patch):
    return patch("h.services.user_signup.TaskData")
