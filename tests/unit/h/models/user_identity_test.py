import pytest
import sqlalchemy.exc

from h import models


class TestUserIdentity:
    def test_you_can_save_and_then_retrieve_field_values(self, db_session, user):
        user_identity_1 = models.UserIdentity(
            provider="provider_1", provider_unique_id="1", user=user
        )
        user_identity_2 = models.UserIdentity(
            provider="provider_1", provider_unique_id="2", user=user
        )
        user_identity_3 = models.UserIdentity(
            provider="provider_2", provider_unique_id="3", user=user
        )

        db_session.add_all([user_identity_1, user_identity_2, user_identity_3])
        db_session.flush()

        user_identities = (
            db_session.query(models.UserIdentity)
            .order_by(models.UserIdentity.provider_unique_id)
            .all()
        )

        # Auto incrementing unique IDs should have been generated for us.
        assert isinstance(user_identities[0].id, int)
        assert isinstance(user_identities[1].id, int)
        assert isinstance(user_identities[2].id, int)

        # The provider strings that we gave should have been saved.
        assert user_identities[0].provider == "provider_1"
        assert user_identities[1].provider == "provider_1"
        assert user_identities[2].provider == "provider_2"

        # The provider_unique_id strings that we gave should have been saved.
        assert user_identities[0].provider_unique_id == "1"
        assert user_identities[1].provider_unique_id == "2"
        assert user_identities[2].provider_unique_id == "3"

    def test_provider_cant_be_null(self, db_session, user):
        db_session.add(models.UserIdentity(provider_unique_id="1", user=user))

        with pytest.raises(
            sqlalchemy.exc.IntegrityError,
            match='null value in column "provider" violates not-null constraint',
        ):
            db_session.flush()

    def test_provider_id_cant_be_null(self, db_session, user):
        db_session.add(models.UserIdentity(provider="provider", user=user))

        with pytest.raises(
            sqlalchemy.exc.IntegrityError,
            match='null value in column "provider_unique_id" violates not-null constraint',
        ):
            db_session.flush()

    def test_user_cant_be_null(self, db_session):
        db_session.add(models.UserIdentity(provider="provider", provider_unique_id="1"))

        with pytest.raises(
            sqlalchemy.exc.IntegrityError,
            match='null value in column "user_id" violates not-null constraint',
        ):
            db_session.flush()

    def test_two_cant_have_the_same_provider_and_provider_id(
        self, db_session, factories
    ):
        db_session.add_all(
            [
                models.UserIdentity(
                    provider="provider", provider_unique_id="id", user=factories.User()
                ),
                models.UserIdentity(
                    provider="provider", provider_unique_id="id", user=factories.User()
                ),
            ]
        )

        with pytest.raises(
            sqlalchemy.exc.IntegrityError,
            match='duplicate key value violates unique constraint "uq__user_identity__provider"',
        ):
            db_session.flush()

    def test_one_user_can_have_the_same_provider_id_from_different_providers(
        self, db_session, user
    ):
        db_session.add_all(
            [
                models.UserIdentity(
                    provider="provider_1", provider_unique_id="id", user=user
                ),
                models.UserIdentity(
                    provider="provider_2", provider_unique_id="id", user=user
                ),
            ]
        )

        db_session.flush()

    def test_different_users_can_have_the_same_provider_id_from_different_providers(
        self, db_session, factories
    ):
        db_session.add_all(
            [
                models.UserIdentity(
                    provider="provider_1",
                    provider_unique_id="id",
                    user=factories.User(),
                ),
                models.UserIdentity(
                    provider="provider_2",
                    provider_unique_id="id",
                    user=factories.User(),
                ),
            ]
        )

        db_session.flush()

    def test_removing_a_user_identity_from_a_user_deletes_the_user_identity_from_the_db(
        self, db_session, user
    ):
        # Add a couple of noise UserIdentity's. These should not be removed
        # from the DB.
        models.UserIdentity(provider="provider", provider_unique_id="1", user=user)
        models.UserIdentity(provider="provider", provider_unique_id="2", user=user)
        # The UserIdentity that we are going to remove.
        user_identity = models.UserIdentity(
            provider="provider", provider_unique_id="3", user=user
        )

        user.identities.remove(user_identity)

        assert user_identity not in db_session.query(models.UserIdentity).all()

    def test_deleting_a_user_identity_removes_it_from_its_user(self, db_session, user):
        # Add a couple of noise UserIdentity's. These should not be removed
        # from user.identities.
        models.UserIdentity(provider="provider", provider_unique_id="1", user=user)
        models.UserIdentity(provider="provider", provider_unique_id="2", user=user)
        # The UserIdentity that we are going to remove.
        user_identity = models.UserIdentity(
            provider="provider", provider_unique_id="3", user=user
        )
        db_session.commit()

        db_session.delete(user_identity)

        db_session.refresh(user)  # Make sure user.identities is up to date.
        assert user_identity not in user.identities

    def test_deleting_a_user_deletes_all_its_user_identities(self, db_session, user):
        models.UserIdentity(provider="provider", provider_unique_id="1", user=user)
        models.UserIdentity(provider="provider", provider_unique_id="2", user=user)
        db_session.commit()

        db_session.delete(user)

        assert not db_session.query(models.UserIdentity).count()

    def test_repr(self):
        user_identity = models.UserIdentity(
            provider="provider_1", provider_unique_id="1"
        )

        expected_repr = "UserIdentity(provider='provider_1', provider_unique_id='1')"

        assert repr(user_identity) == expected_repr

    @pytest.fixture
    def user(self, factories):
        return factories.User()
