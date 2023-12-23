from datetime import datetime, timedelta

import pytest
from sqlalchemy import exc
from sqlalchemy.sql.elements import BinaryExpression

from h.models import Activation
from h.models.user import User, UserIDComparator


class TestUserIDComparator:
    @pytest.mark.parametrize("other", (None, "acct:username@authority"))
    def test__eq__returns_a_BinaryExpression(self, comparator, other):
        # We don't actually get a True here, just something which might
        # evaluate to true in the DB
        assert isinstance(comparator == other, BinaryExpression)

    @pytest.mark.parametrize(
        "non_matching",
        ("not_a_valid_user_id", "acct:DIFFERENT@authority", "acct:username@DIFFERENT"),
    )
    def test__eq___returns_False(self, comparator, non_matching):
        assert not comparator == non_matching

    @pytest.fixture
    def comparator(self):
        return UserIDComparator("username", "authority")


class TestUserModelDataConstraints:
    """Unit tests for :py:module:`h.models.User` data integrity constraints."""

    def test_cannot_create_dot_variant_of_user(self, db_session, fred):
        db_session.add(
            User(authority=fred.authority, username="fred.bloggs", email=fred.email)
        )
        with pytest.raises(exc.IntegrityError):
            db_session.flush()

    def test_cannot_create_case_variant_of_user(self, db_session):
        bob = User(
            authority="example.com", username="BobJones", email="bob@example.com"
        )
        bob2 = User(
            authority="example.com", username="bobjones", email="bob@example.org"
        )

        db_session.add(bob)
        db_session.add(bob2)
        with pytest.raises(exc.IntegrityError):
            db_session.flush()

    def test_filtering_by_username_matches_dot_variant_of_user(self, db_session, fred):
        result = db_session.query(User).filter_by(username="fred.bloggs").one()

        assert result == fred

    def test_filtering_by_username_matches_dot_variant_of_user_using_in(
        self, db_session, fred
    ):
        result = (
            db_session.query(User)
            .filter(User.username.in_(["Fred.bloggs"]))  # pylint:disable=no-member
            .one()
        )

        assert result == fred

    def test_filtering_by_username_matches_case_variant_of_user(self, db_session, fred):
        result = db_session.query(User).filter_by(username="FredBloggs").one()

        assert result == fred

    def test_userid_derived_from_username_and_authority(self, fred):
        assert fred.userid == "acct:fredbloggs@example.com"

    def test_cannot_create_user_with_too_short_username(self):
        with pytest.raises(ValueError):
            User(username="aa")

    def test_cannot_create_user_with_too_long_username(self):
        with pytest.raises(ValueError):
            User(username="1234567890123456789012345678901")

    def test_cannot_create_user_with_invalid_chars(self):
        with pytest.raises(ValueError):
            User(username="foo-bar")

    def test_cannot_create_user_with_too_long_email(self):
        with pytest.raises(ValueError):
            User(email="bob@b" + "o" * 100 + "b.com")

    def test_can_create_user_with_null_email(self):
        User(email=None)

    def test_can_change_email_to_null(self):
        user = User(email="bob@bob.com")

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


class TestUserModelUserId:
    def test_userid_equals_query(self, db_session, fred):
        result = (
            db_session.query(User).filter_by(userid="acct:fredbloggs@example.com").one()
        )

        assert result == fred

    def test_userid_equals_query_with_invalid_userid(self, db_session):
        # This is to ensure that we don't expose the InvalidUserId that could
        # potentially be thrown by split_user.

        result = db_session.query(User).filter_by(userid="fredbloggsexample.com").all()

        assert result == []

    def test_userid_in_query(self, db_session, fred):
        alice = User(
            authority="foobar.com", username="alicewrites", email="alice@foobar.com"
        )
        db_session.add(alice)
        db_session.flush()

        result = (
            db_session.query(User)
            .filter(
                User.userid.in_(  # pylint:disable=no-member
                    [
                        "acct:fredbloggs@example.com",
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

    def test_userid_in_query_with_invalid_userid_mixed_in(self, db_session, fred):
        # This is to ensure that we don't expose the InvalidUserId that could
        # potentially be thrown by split_user.
        result = (
            db_session.query(User)
            .filter(
                # pylint:disable=no-member
                User.userid.in_(["acct:fredbloggs@example.com", "invalid"])
            )
            .all()
        )

        assert len(result) == 1
        assert fred in result

    def test_userid_in_query_with_only_invalid_userid(self, db_session):
        # This is to ensure that we don't expose the InvalidUserId that could
        # potentially be thrown by split_user.

        result = (
            db_session.query(User)
            .filter(
                User.userid.in_(["fredbloggsexample.net"])  # pylint:disable=no-member
            )
            .all()
        )

        assert result == []


class TestUserModel:
    def test_activate_activates_user(self, user, db_session):
        user.activate()
        db_session.flush()

        assert user.is_activated

    def test_activate_updates_activation_date(self, user):
        assert user.activation_date is None

        user.activate()

        assert isinstance(user.activation_date, datetime)

        # We can't test for the exact time, but this should be close
        assert user.activation_date - datetime.utcnow() < timedelta(seconds=1)

    def test_privacy_accepted_defaults_to_None(self):
        # nullable
        assert getattr(User(), "privacy_accepted") is None

    def test_repr(self, user):
        assert repr(user) == "<User: kiki>"

    @pytest.fixture
    def user(self, db_session):
        user = User(authority="example.com", username="kiki", email="kiki@kiki.com")
        user.activation = Activation()
        db_session.add(user)
        db_session.flush()

        return user


class TestUserGetByEmail:
    def test_it_returns_a_user(self, db_session, users):
        user = users["meredith"]
        actual = User.get_by_email(db_session, user.email, user.authority)
        assert actual == user

    @pytest.mark.usefixtures("users")
    def test_it_filters_by_email(self, db_session):
        authority = "example.com"
        email = "bogus@msn.com"

        actual = User.get_by_email(db_session, email, authority)
        assert actual is None

    def test_it_filters_email_case_insensitive(self, db_session, users):
        user = users["emily"]
        mixed_email = "eMiLy@mSn.com"

        actual = User.get_by_email(db_session, mixed_email, user.authority)
        assert actual == user

    def test_it_filters_by_authority(self, db_session, users):
        user = users["norma"]

        actual = User.get_by_email(db_session, user.email, "example.com")
        assert actual is None

    def test_you_cannot_get_users_with_no_emails(self, db_session):
        assert not User.get_by_email(db_session, None, "example.com")

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


class TestUserGetByActivation:
    def test_it(self, db_session, factories):
        activated_user = factories.User(activation=factories.Activation())

        user = User.get_by_activation(db_session, activated_user.activation)

        assert user == activated_user

    def test_it_with_no_matches(self, db_session, factories):
        activation = factories.Activation()

        user = User.get_by_activation(db_session, activation)

        assert user is None


class TestUserGetByUsername:
    def test_it_returns_a_user(self, db_session, users):
        user = users["meredith"]

        actual = User.get_by_username(db_session, user.username, user.authority)
        assert actual == user

    def test_it_filters_by_username(self, db_session):
        authority = "example.com"
        username = "bogus"

        actual = User.get_by_username(db_session, username, authority)
        assert actual is None

    def test_it_filters_by_authority(self, db_session, users):
        user = users["norma"]

        actual = User.get_by_username(db_session, user.username, "example.com")
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


@pytest.fixture
def fred(db_session):
    fred = User(authority="example.com", username="fredbloggs", email="fred@email.com")

    db_session.add(fred)
    db_session.flush()
    return fred
