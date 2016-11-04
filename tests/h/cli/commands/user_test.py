# -*- coding: utf-8 -*-

import mock
import pytest

from h import models
from h.cli.commands import user as user_cli


class TestAdminCommand(object):
    def test_it_adds_admin(self, cli, cliconfig, non_admin_user, db_session):
        result = cli.invoke(user_cli.admin,
                            [u'--on', non_admin_user.username],
                            obj=cliconfig)

        assert result.exit_code == 0

        user = db_session.query(models.User).get(non_admin_user.id)
        assert user.admin

    def test_it_adds_admin_by_default(self, cli, cliconfig, non_admin_user, db_session):
        result = cli.invoke(user_cli.admin,
                            [non_admin_user.username],
                            obj=cliconfig)

        assert result.exit_code == 0

        user = db_session.query(models.User).get(non_admin_user.id)
        assert user.admin

    def test_it_adds_admin_with_specific_authority(self, cli, cliconfig, non_admin_user, db_session):
        non_admin_user.authority = u'partner.org'
        db_session.flush()

        result = cli.invoke(user_cli.admin,
                            [u'--authority', u'partner.org', non_admin_user.username],
                            obj=cliconfig)

        assert result.exit_code == 0

        user = db_session.query(models.User).get(non_admin_user.id)
        assert user.admin

    def test_it_removes_admin(self, cli, cliconfig, admin_user, db_session):
        result = cli.invoke(user_cli.admin,
                            [u'--off', admin_user.username],
                            obj=cliconfig)

        assert result.exit_code == 0

        user = db_session.query(models.User).get(admin_user.id)
        assert not user.admin

    def test_it_removes_admin_with_specific_authority(self, cli, cliconfig, admin_user, db_session):
        admin_user.authority = u'partner.org'

        result = cli.invoke(user_cli.admin,
                            [u'--off', u'--authority', u'partner.org', admin_user.username],
                            obj=cliconfig)

        assert result.exit_code == 0

        user = db_session.query(models.User).get(admin_user.id)
        assert not user.admin

    def test_it_errors_when_user_could_not_be_found(self, cli, cliconfig, non_admin_user, db_session):
        result = cli.invoke(user_cli.admin,
                            ['bogus_%s' % non_admin_user.username],
                            obj=cliconfig)

        assert result.exit_code == 1
        user = db_session.query(models.User).get(non_admin_user.id)
        assert not user.admin

    def test_it_errors_when_user_with_specific_authority_could_not_be_found(
            self, cli, cliconfig, non_admin_user, db_session):

        result = cli.invoke(user_cli.admin,
                            ['--authority', 'foo.com', non_admin_user.username],
                            obj=cliconfig)

        assert result.exit_code == 1
        user = db_session.query(models.User).get(non_admin_user.id)
        assert not user.admin

    @pytest.fixture
    def cliconfig(self, pyramid_request):
        pyramid_request.tm = mock.Mock()
        return {'bootstrap': mock.Mock(return_value=pyramid_request)}

    @pytest.fixture
    def admin_user(self, db_session, factories):
        return self._user(db_session, factories, True)

    @pytest.fixture
    def non_admin_user(self, db_session, factories):
        return self._user(db_session, factories, False)

    def _user(self, db_session, factories, admin):
        user = factories.User(admin=admin)
        db_session.add(user)
        db_session.flush()
        return user
