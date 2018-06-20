# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest
import sqlalchemy.exc

from h import models


class TestUserIdentity(object):
    def test_you_can_save_and_then_retrieve_field_values(self, db_session, matchers):
        user_identity_1 = models.UserIdentity(
            provider="provider_1", provider_unique_id="1"
        )
        user_identity_2 = models.UserIdentity(
            provider="provider_1", provider_unique_id="2"
        )
        user_identity_3 = models.UserIdentity(
            provider="provider_2", provider_unique_id="3"
        )

        db_session.add_all([user_identity_1, user_identity_2, user_identity_3])
        db_session.flush()

        user_identities = (
            db_session.query(models.UserIdentity)
            .order_by(models.UserIdentity.provider_unique_id)
            .all()
        )

        # Auto incrementing unique IDs should have been generated for us.
        assert type(user_identities[0].id) is int
        assert type(user_identities[1].id) is int
        assert type(user_identities[2].id) is int

        # The provider strings that we gave should have been saved.
        assert user_identities[0].provider == "provider_1"
        assert user_identities[1].provider == "provider_1"
        assert user_identities[2].provider == "provider_2"

        # The provider_unique_id strings that we gave should have been saved.
        assert user_identities[0].provider_unique_id == "1"
        assert user_identities[1].provider_unique_id == "2"
        assert user_identities[2].provider_unique_id == "3"

    def test_provider_cant_be_null(self, db_session):
        db_session.add(models.UserIdentity(provider_unique_id="1"))

        with pytest.raises(
            sqlalchemy.exc.IntegrityError,
            match='null value in column "provider" violates not-null constraint',
        ):
            db_session.flush()

    def test_provider_id_cant_be_null(self, db_session):
        db_session.add(models.UserIdentity(provider="provider"))

        with pytest.raises(
            sqlalchemy.exc.IntegrityError,
            match='null value in column "provider_unique_id" violates not-null constraint',
        ):
            db_session.flush()

    def test_two_cant_have_the_same_provider_and_provider_id(self, db_session):
        db_session.add_all(
            [
                models.UserIdentity(provider="provider", provider_unique_id="id"),
                models.UserIdentity(provider="provider", provider_unique_id="id"),
            ]
        )

        with pytest.raises(
            sqlalchemy.exc.IntegrityError,
            match='duplicate key value violates unique constraint "uq__user_identity__provider"',
        ):
            db_session.flush()

    def test_two_can_have_the_same_provider_id_but_different_providers(
        self, db_session
    ):
        db_session.add_all(
            [
                models.UserIdentity(provider="provider_1", provider_unique_id="id"),
                models.UserIdentity(provider="provider_2", provider_unique_id="id"),
            ]
        )

        db_session.flush()
