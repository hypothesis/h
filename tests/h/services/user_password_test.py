import pytest
from passlib.context import CryptContext

from h.security import password_context
from h.services.user_password import UserPasswordService


class TestUserPasswordService:
    def test_check_password_false_with_null_password(self, svc, user):
        assert not svc.check_password(user, "anything")

    def test_check_password_false_with_empty_password(self, svc, user):
        user.password = ""

        assert not svc.check_password(user, "")

    def test_check_password_true_with_matching_password(self, svc, user):
        svc.update_password(user, "s3cr37")

        assert svc.check_password(user, "s3cr37")

    def test_check_password_false_with_incorrect_password(self, svc, user):
        svc.update_password(user, "s3cr37")

        assert not svc.check_password(user, "somethingelse")

    def test_check_password_validates_old_style_passwords(self, svc, user):
        user.salt = "somesalt"
        # Generated with passlib.hash.bcrypt.hash('foobar' + 'somesalt', rounds=4)
        user.password = "$2a$04$zDQnlV/YBG.ju2i14V15p.5nWYL52ZBqjGsBWgLAisGkEJw812BHy"

        assert not svc.check_password(user, "somethingelse")
        assert svc.check_password(user, "foobar")

    def test_check_password_upgrades_old_style_passwords(self, hasher, svc, user):
        user.salt = "somesalt"
        # Generated with passlib.hash.bcrypt.hash('foobar' + 'somesalt', rounds=4)
        user.password = "$2a$04$zDQnlV/YBG.ju2i14V15p.5nWYL52ZBqjGsBWgLAisGkEJw812BHy"

        svc.check_password(user, "foobar")

        assert user.salt is None
        assert not hasher.needs_update(user.password)

    def test_check_password_only_upgrades_when_password_is_correct(
        self, hasher, svc, user
    ):
        user.salt = "somesalt"
        # Generated with passlib.hash.bcrypt.hash('foobar' + 'somesalt', rounds=4)
        user.password = "$2a$04$zDQnlV/YBG.ju2i14V15p.5nWYL52ZBqjGsBWgLAisGkEJw812BHy"

        svc.check_password(user, "donkeys")

        assert user.salt is not None
        assert hasher.needs_update(user.password)

    def test_check_password_works_after_upgrade(self, svc, user):
        user.salt = "somesalt"
        # Generated with passlib.hash.bcrypt.hash('foobar' + 'somesalt', rounds=4)
        user.password = "$2a$04$zDQnlV/YBG.ju2i14V15p.5nWYL52ZBqjGsBWgLAisGkEJw812BHy"

        svc.check_password(user, "foobar")

        assert svc.check_password(user, "foobar")

    def test_check_password_upgrades_new_style_passwords(self, hasher, svc, user):
        # Generated with passlib.hash.bcrypt.hash('foobar', rounds=4, ident='2b')
        user.password = "$2b$04$L2j.vXxlLt9JJNHHsy0EguslcaphW7vssSpHbhqCmf9ECsMiuTd1y"

        svc.check_password(user, "foobar")

        assert not hasher.needs_update(user.password)

    def test_updating_password_unsets_salt(self, svc, user):
        user.salt = "somesalt"
        user.password = "whatever"

        svc.update_password(user, "flibble")

        assert user.salt is None
        assert svc.check_password(user, "flibble")

    def test_uses_global_password_context_by_default(self):
        svc = UserPasswordService()
        assert svc.hasher == password_context

    @pytest.fixture
    def hasher(self):
        # Use a much faster hasher for testing purposes. DO NOT use as few as
        # 5 rounds of bcrypt in production code under ANY CIRCUMSTANCES.
        return CryptContext(
            schemes=["bcrypt"],
            bcrypt__ident="2b",
            bcrypt__min_rounds=5,
            bcrypt__max_rounds=5,
        )

    @pytest.fixture
    def svc(self, hasher):
        svc = UserPasswordService()
        svc.hasher = hasher
        return svc

    @pytest.fixture
    def user(self, factories):
        return factories.User.build()
