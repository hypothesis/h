from unittest import mock

import pytest
from sqlalchemy.exc import SQLAlchemyError

from h.services.exceptions import ConflictError, ValidationError
from h.services.user_update import UserUpdateService, user_update_factory


class TestUserUpdate:
    def test_it_updates_valid_user_attrs(self, factories, svc):
        user = factories.User()
        data = {"display_name": "foobar", "email": "foobar@example.com"}

        svc.update(user, **data)

        assert user.display_name == "foobar"
        assert user.email == "foobar@example.com"

    def test_it_returns_updated_user_model(self, factories, svc):
        user = factories.User()
        data = {"display_name": "whatnot"}

        updated_user = svc.update(user, **data)

        assert updated_user == user

    def test_it_does_not_protect_against_undefined_properties(self, factories, svc):
        user = factories.User()
        data = {"some_random_field": "whatever"}

        updated_user = svc.update(user, **data)

        # This won't be persisted in the DB, of course, but the model instance
        # doesn't have a problem with it
        assert updated_user.some_random_field == "whatever"

    def test_it_raises_ValidationError_if_authority_present_in_kwargs(
        self, factories, svc
    ):
        user = factories.User()

        with pytest.raises(
            ValidationError, match="A user's authority may not be changed"
        ):
            svc.update(user, authority="something.com")

    def test_it_raises_ValidationError_if_email_fails_model_validation(
        self, factories, svc
    ):
        user = factories.User()

        with pytest.raises(
            ValidationError, match="email must be less than.*characters long"
        ):
            svc.update(user, email="o" * 150)

    def test_it_raises_ValidationError_if_username_fails_model_validation(
        self, factories, svc
    ):
        user = factories.User()

        with pytest.raises(
            ValidationError, match="username must be between.*characters long"
        ):
            svc.update(user, username="lo")

    def test_it_will_not_raise_on_malformed_email(self, factories, svc):
        user = factories.User()

        # It's up to callers to validate email at this point
        updated_user = svc.update(user, email="fingers")

        assert updated_user.email == "fingers"

    def test_it_raises_ConflictError_on_username_authority_uniqueness_violation(
        self, factories, svc
    ):
        factories.User(username="user1", authority="baz.com")
        user2 = factories.User(username="user2", authority="baz.com")

        with pytest.raises(ConflictError, match="username"):
            svc.update(user2, username="user1")

    def test_it_raises_on_any_other_SQLAlchemy_exception(self, factories):
        fake_session = mock.Mock()
        fake_session.flush.side_effect = SQLAlchemyError("foo")

        update_svc = UserUpdateService(session=fake_session)
        user = factories.User()

        with pytest.raises(SQLAlchemyError):
            update_svc.update(user, username="fingers")


class TestFactory:
    def test_returns_user_update_service(self, pyramid_request):
        user_update_service = user_update_factory(None, pyramid_request)

        assert isinstance(user_update_service, UserUpdateService)


@pytest.fixture
def svc(db_session):
    return UserUpdateService(session=db_session)
