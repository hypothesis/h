# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest
from sqlalchemy import exc
from pyramid.authorization import ACLAuthorizationPolicy

from h import models


class TestUserModelDataConstraints(object):
    """Unit tests for :py:module:`h.models.User` data integrity constraints"""

    def test_cannot_create_dot_variant_of_user(self, db_session):
        fred = models.User(
            authority="example.com", username="fredbloggs", email="fred@example.com"
        )
        fred2 = models.User(
            authority="example.com", username="fred.bloggs", email="fred@example.org"
        )

        db_session.add(fred)
        db_session.add(fred2)
        with pytest.raises(exc.IntegrityError):
            db_session.flush()

    def test_cannot_create_case_variant_of_user(self, db_session):
        bob = models.User(
            authority="example.com", username="BobJones", email="bob@example.com"
        )
        bob2 = models.User(
            authority="example.com", username="bobjones", email="bob@example.org"
        )

        db_session.add(bob)
        db_session.add(bob2)
        with pytest.raises(exc.IntegrityError):
            db_session.flush()

    def test_filtering_by_username_matches_dot_variant_of_user(self, db_session):
        fred = models.User(
            authority="example.com", username="fredbloggs", email="fred@example.com"
        )
        db_session.add(fred)
        db_session.flush()

        result = db_session.query(models.User).filter_by(username="fred.bloggs").one()

        assert result == fred

    def test_filtering_by_username_matches_case_variant_of_user(self, db_session):
        fred = models.User(
            authority="example.com", username="fredbloggs", email="fred@example.com"
        )
        db_session.add(fred)
        db_session.flush()

        result = db_session.query(models.User).filter_by(username="FredBloggs").one()

        assert result == fred

    def test_userid_derived_from_username_and_authority(self):
        fred = models.User(
            authority="example.net", username="fredbloggs", email="fred@example.com"
        )

        assert fred.userid == "acct:fredbloggs@example.net"

    def test_cannot_create_user_with_too_short_username(self):
        with pytest.raises(ValueError):
            models.User(username="aa")

    def test_cannot_create_user_with_too_long_username(self):
        with pytest.raises(ValueError):
            models.User(username="1234567890123456789012345678901")

    def test_cannot_create_user_with_invalid_chars(self):
        with pytest.raises(ValueError):
            models.User(username="foo-bar")

    def test_cannot_create_user_with_too_long_email(self):
        with pytest.raises(ValueError):
            models.User(email="bob@b" + "o" * 100 + "b.com")

    def test_can_create_user_with_null_email(self):
        models.User(email=None)

    def test_can_change_email_to_null(self):
        user = models.User(email="bob@bob.com")

        user.email = None

    def test_cannot_create_two_users_with_same_non_null_email_and_authority(
        self, db_session, factories
    ):
        factories.User(email="bob@bob.com", authority="hypothes.is")
        factories.User(email="bob@bob.com", authority="hypothes.is")

        with pytest.raises(
            exc.IntegrityError,
            match='duplicate key value violates unique constraint "uq__user__email"',
        ):
            db_session.flush()

    def test_can_create_two_users_with_same_null_email_and_authority(
        self, db_session, factories
    ):
        factories.User(email=None, authority="hypothes.is")
        factories.User(email=None, authority="hypothes.is")

        db_session.flush()


class TestUserModelUserId(object):
    def test_userid_equals_query(self, db_session):
        fred = models.User(
            authority="example.net", username="fredbloggs", email="fred@example.com"
        )
        db_session.add(fred)
        db_session.flush()

        result = (
            db_session.query(models.User)
            .filter_by(userid="acct:fredbloggs@example.net")
            .one()
        )

        assert result == fred

    def test_userid_equals_query_with_invalid_userid(self, db_session):
        # This is to ensure that we don't expose the ValueError that could
        # potentially be thrown by split_user.

        result = (
            db_session.query(models.User)
            .filter_by(userid="fredbloggsexample.net")
            .all()
        )

        assert result == []

    def test_userid_in_query(self, db_session):
        fred = models.User(
            authority="example.net", username="fredbloggs", email="fred@example.net"
        )
        alice = models.User(
            authority="foobar.com", username="alicewrites", email="alice@foobar.com"
        )
        db_session.add_all([fred, alice])
        db_session.flush()

        result = (
            db_session.query(models.User)
            .filter(
                models.User.userid.in_(
                    [
                        "acct:fredbloggs@example.net",
                        "acct:alicewrites@foobar.com",
                        "acct:missing@bla.org",
                    ]
                )
            )
            .all()
        )

        assert len(result) == 2
        assert fred in result
        assert alice in result

    def test_userid_in_query_with_invalid_userid_mixed_in(self, db_session):
        # This is to ensure that we don't expose the ValueError that could
        # potentially be thrown by split_user.

        fred = models.User(
            authority="example.net", username="fredbloggs", email="fred@example.com"
        )
        db_session.add(fred)
        db_session.flush()

        result = (
            db_session.query(models.User)
            .filter(models.User.userid.in_(["acct:fredbloggs@example.net", "invalid"]))
            .all()
        )

        assert len(result) == 1
        assert fred in result

    def test_userid_in_query_with_only_invalid_userid(self, db_session):
        # This is to ensure that we don't expose the ValueError that could
        # potentially be thrown by split_user.

        result = (
            db_session.query(models.User)
            .filter(models.User.userid.in_(["fredbloggsexample.net"]))
            .all()
        )

        assert result == []


class TestUserModel(object):
    def test_User_activate_activates_user(self, db_session):
        user = models.User(
            authority="example.com", username="kiki", email="kiki@kiki.com"
        )
        activation = models.Activation()
        user.activation = activation
        db_session.add(user)
        db_session.flush()

        user.activate()
        db_session.commit()

        assert user.is_activated

    def test_privacy_accepted_defaults_to_None(self, db_session):
        # nullable
        assert getattr(models.User(), "privacy_accepted") is None


class TestUserGetByEmail(object):
    def test_it_returns_a_user(self, db_session, users):
        user = users["meredith"]
        actual = models.User.get_by_email(db_session, user.email, user.authority)
        assert actual == user

    def test_it_filters_by_email(self, db_session, users):
        authority = "example.com"
        email = "bogus@msn.com"

        actual = models.User.get_by_email(db_session, email, authority)
        assert actual is None

    def test_it_filters_email_case_insensitive(self, db_session, users):
        user = users["emily"]
        mixed_email = "eMiLy@mSn.com"

        actual = models.User.get_by_email(db_session, mixed_email, user.authority)
        assert actual == user

    def test_it_filters_by_authority(self, db_session, users):
        user = users["norma"]

        actual = models.User.get_by_email(db_session, user.email, "example.com")
        assert actual is None

    def test_you_cannot_get_users_with_no_emails(self, db_session):
        assert not models.User.get_by_email(db_session, None, "example.com")

    @pytest.fixture
    def users(self, db_session, factories):
        users = {
            "emily": factories.User(
                username="emily", email="emily@msn.com", authority="example.com"
            ),
            "norma": factories.User(
                username="norma", email="norma@foo.org", authority="foo.org"
            ),
            "meredith": factories.User(
                username="meredith", email="meredith@gmail.com", authority="example.com"
            ),
            "bob": factories.User(username="bob", email=None, authority="example.com"),
        }
        db_session.flush()
        return users


class TestUserGetByUsername(object):
    def test_it_returns_a_user(self, db_session, users):
        user = users["meredith"]

        actual = models.User.get_by_username(db_session, user.username, user.authority)
        assert actual == user

    def test_it_filters_by_username(self, db_session):
        authority = "example.com"
        username = "bogus"

        actual = models.User.get_by_username(db_session, username, authority)
        assert actual is None

    def test_it_filters_by_authority(self, db_session, users):
        user = users["norma"]

        actual = models.User.get_by_username(db_session, user.username, "example.com")
        assert actual is None

    @pytest.fixture
    def users(self, db_session, factories):
        users = {
            "emily": factories.User(username="emily", authority="example.com"),
            "norma": factories.User(username="norma", authority="foo.org"),
            "meredith": factories.User(username="meredith", authority="example.com"),
        }
        db_session.flush()
        return users


class TestUserACL(object):
    def test_auth_client_with_matching_authority_may_update_user(
        self, user, authz_policy
    ):
        user.authority = "weewhack.com"

        assert authz_policy.permits(
            user, ["flip", "client_authority:weewhack.com"], "update"
        )

    def test_auth_client_without_matching_authority_may_not_update_user(
        self, user, authz_policy
    ):
        user.authority = "weewhack.com"

        assert not authz_policy.permits(
            user, ["flip", "client_authority:2weewhack.com"], "update"
        )

    def test_user_with_authority_may_not_update_user(self, user, authz_policy):
        user.authority = "fabuloso.biz"

        assert not authz_policy.permits(
            user, ["flip", "authority:fabuloso.biz"], "update"
        )

    @pytest.fixture
    def authz_policy(self):
        return ACLAuthorizationPolicy()

    @pytest.fixture
    def user(self):
        user = models.User(username="filip", authority="example.com")
        return user
