from unittest import mock

import pytest

from h.services.user_unique import (
    DuplicateUserError,
    UserUniqueService,
    user_unique_factory,
)


class TestUserUniqueEnsureUnique:
    def test_it_raises_if_email_uniqueness_violated(self, svc, user, pyramid_request):
        dupe_email = user.email

        with pytest.raises(
            DuplicateUserError,
            match=(f".*user with email address '{dupe_email}' already exists"),
        ):
            svc.ensure_unique(
                {"email": dupe_email}, authority=pyramid_request.default_authority
            )

    def test_it_allows_duplicate_email_at_different_authority(self, svc, user):
        svc.ensure_unique({"email": user.email}, authority="foo.com")

    def test_it_raises_if_username_uniqueness_violated(
        self, svc, user, pyramid_request
    ):
        dupe_username = user.username

        with pytest.raises(
            DuplicateUserError,
            match=(f".*user with username '{dupe_username}' already exists"),
        ):
            svc.ensure_unique(
                {"username": dupe_username}, authority=pyramid_request.default_authority
            )

    def test_it_allows_duplicate_username_at_different_authority(self, svc, user):
        svc.ensure_unique({"username": user.username}, authority="foo.com")

    def test_it_raises_if_identities_uniqueness_violated(self, svc, pyramid_request):
        dupe_identity = {"provider": "provider_a", "provider_unique_id": "123"}

        with pytest.raises(
            DuplicateUserError,
            match=".*provider 'provider_a' and unique id '123' already exists",
        ):
            svc.ensure_unique(
                {"identities": [dupe_identity]},
                authority=pyramid_request.default_authority,
            )

    def test_it_raises_if_identities_uniqueness_violated_at_different_authority(
        self, svc
    ):
        # note that this is different from email and username behavior
        dupe_identity = {"provider": "provider_a", "provider_unique_id": "123"}
        with pytest.raises(
            DuplicateUserError,
            match=".*provider 'provider_a' and unique id '123' already exists",
        ):
            svc.ensure_unique({"identities": [dupe_identity]}, authority="foo.com")

    def test_it_proxies_email_lookup_to_model(
        self, svc, user_model, db_session, pyramid_request
    ):
        svc.ensure_unique({"email": "foo@bar.com"}, pyramid_request.default_authority)

        user_model.get_by_email.assert_called_once_with(
            db_session, "foo@bar.com", pyramid_request.default_authority
        )

    def test_it_proxies_username_lookup_to_model(
        self, svc, user_model, db_session, pyramid_request
    ):
        svc.ensure_unique({"username": "fernando"}, pyramid_request.default_authority)

        user_model.get_by_username.assert_called_once_with(
            db_session, "fernando", pyramid_request.default_authority
        )

    def test_it_proxies_identity_fetching_to_user_service(
        self, svc, user_service, pyramid_request
    ):
        identity_data = [
            {"provider": "provider_a", "provider_unique_id": "123"},
            {"provider": "provider_a", "provider_unique_id": "123"},
        ]
        user_service.fetch_by_identity.return_value = None

        svc.ensure_unique(
            {"identities": identity_data}, authority=pyramid_request.default_authority
        )

        user_service.fetch_by_identity.assert_has_calls(
            [
                mock.call(
                    identity_data[0]["provider"], identity_data[0]["provider_unique_id"]
                ),
                mock.call(
                    identity_data[1]["provider"], identity_data[1]["provider_unique_id"]
                ),
            ]
        )

    def test_it_does_not_fetch_by_username_if_not_present(
        self, svc, user_model, pyramid_request
    ):
        svc.ensure_unique({"email": "foo@bar.com"}, pyramid_request.default_authority)

        user_model.get_by_username.assert_not_called()

    def test_it_does_not_fetch_by_email_if_not_present(
        self, svc, user_model, pyramid_request
    ):
        svc.ensure_unique({"username": "doodle"}, pyramid_request.default_authority)

        user_model.get_by_email.assert_not_called()

    def test_it_allows_empty_data(self, svc, pyramid_request):
        svc.ensure_unique({}, authority=pyramid_request.default_authority)
        # does not raise

    def test_it_combines_error_messages(self, svc, user, pyramid_request):
        dupe_identity = {
            "provider": user.identities[0].provider,
            "provider_unique_id": user.identities[0].provider_unique_id,
        }
        with pytest.raises(DuplicateUserError, match=".*email.*username.*provider"):
            svc.ensure_unique(
                {
                    "email": user.email,
                    "username": user.username,
                    "identities": [dupe_identity],
                },
                authority=pyramid_request.default_authority,
            )

    def test_it_raises_if_authority_missing(self, svc):
        with pytest.raises(TypeError):
            svc.ensure_unique({})


@pytest.mark.usefixtures("user_service")
class TestUserUniqueFactory:
    def test_user_unique_factory(self, pyramid_request):
        svc = user_unique_factory(None, pyramid_request)

        assert isinstance(svc, UserUniqueService)


@pytest.fixture
def user(factories, pyramid_request):
    user = factories.User(
        username="fernando",
        email="foo@example.com",
        authority=pyramid_request.default_authority,
    )
    user.identities = [
        factories.UserIdentity(
            provider="provider_a", provider_unique_id="123", user=user
        )
    ]
    return user


@pytest.fixture
def user_model(patch):
    patched = patch("h.services.user_unique.models.User")
    # By default, a mocked method will return another Mock
    patched.get_by_email.return_value = None
    patched.get_by_username.return_value = None
    return patched


@pytest.fixture
def svc(db_session, user_service):
    return UserUniqueService(session=db_session, user_service=user_service)
