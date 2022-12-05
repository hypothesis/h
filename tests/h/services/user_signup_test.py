import datetime
from unittest.mock import sentinel

import pytest
from sqlalchemy.exc import IntegrityError

from h.models import Activation, User
from h.services.exceptions import ConflictError
from h.services.user_signup import UserSignupService, user_signup_service_factory


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
        now = datetime.datetime.utcnow()
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

    def test_signup_raises_with_invalid_identities(self, svc):
        dupe_identity = {"provider": "a", "provider_unique_id": 1}
        with pytest.raises(
            IntegrityError, match="violates unique constraint.*identity"
        ):
            svc.signup(
                username="foo",
                email="foo@bar.com",
                identities=[dupe_identity, dupe_identity],
            )

    def test_signup_sets_password_using_password_service(
        self, svc, user_password_service
    ):
        user = svc.signup(username="foo", email="foo@bar.com", password="wibble")

        user_password_service.update_password.assert_called_once_with(user, "wibble")

    def test_signup_sends_email(self, svc, signup, tasks_mailer, pyramid_request):
        signup.generate.return_value = ["signup", "args"]

        user = svc.signup(username="foo", email="foo@bar.com")

        signup.generate.assert_called_once_with(
            request=pyramid_request,
            user_id=user.id,
            email="foo@bar.com",
            activation_code=user.activation.code,
        )

        tasks_mailer.send.delay.assert_called_once_with(*signup.generate.return_value)

    def test_signup_does_not_send_email_when_activation_not_required(
        self, svc, signup, tasks_mailer
    ):
        svc.signup(require_activation=False, username="foo", email="foo@bar.com")

        signup.generate.assert_not_called()
        tasks_mailer.send.delay.assert_not_called()

    def test_signup_creates_subscriptions(self, svc, subscription_service, factories):
        subscription = factories.Subscriptions(active=False)
        subscription_service.get_all_subscriptions.return_value = [subscription]
        user = svc.signup(username="foo", email="foo@bar.com")

        subscription_service.get_all_subscriptions.assert_called_once_with(
            user_id=user.userid
        )
        assert subscription.active

    def test_signup_logs_conflict_error_when_account_with_email_already_exists(
        self, svc, patch
    ):
        log = patch("h.services.user_signup.log")

        with pytest.raises(ConflictError):
            svc.signup(username="foo", email="foo@bar.com")
            svc.signup(username="foo", email="foo@bar.com")

        assert (
            "concurrent account signup conflict error occurred during user signup"
            in log.warning.call_args[0][0]
        )

    @pytest.mark.parametrize(
        "username,email",
        [
            # In the real world these values would be identical to the first signup but
            # since we need to force one to error before the other, only the email or
            # only the username matches. Assume that when one of these happens it means
            # the user issued identical signup requests concurrently.
            # Catches Integrity error on identical email.
            ("bar", "foo@bar.com"),
            # Catches Integrity error on identical username.
            ("foo", "foo1@bar.com"),
        ],
    )
    def test_signup_raises_conflict_error_when_account_already_exists(
        self, svc, username, email
    ):
        # This happens when two or more identical
        # concurrent signup requests race each other to the db.
        with pytest.raises(
            ConflictError,
            match=f"The email address {email} has already been registered.",
        ):
            svc.signup(username="foo", email="foo@bar.com")
            svc.signup(username=username, email=email)

    @pytest.fixture
    def svc(self, pyramid_request, user_password_service, subscription_service):
        return UserSignupService(
            request=pyramid_request,
            default_authority="example.org",
            password_service=user_password_service,
            subscription_service=subscription_service,
        )

    @pytest.fixture(autouse=True)
    def tasks_mailer(self, patch):
        return patch("h.services.user_signup.tasks_mailer")

    @pytest.fixture(autouse=True)
    def signup(self, patch):
        return patch("h.services.user_signup.signup")


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
