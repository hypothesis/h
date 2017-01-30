# -*- coding: utf-8 -*-

import mock
import pytest

from h import models
from h.cli.commands import user as user_cli


class TestAddCommand(object):
    def test_it_adds_user_with_default_authority(self, cli, cliconfig, signup_service):
        result = cli.invoke(user_cli.add,
                            [u'--username', u'admin', u'--email', u'admin@localhost',
                             u'--password', u'admin'],
                            obj=cliconfig)

        assert result.exit_code == 0

        signup_service.signup.assert_called_with(username=u'admin',
                                                 email=u'admin@localhost',
                                                 password=u'admin',
                                                 require_activation=False)

    def test_it_adds_user_with_specific_authority(self, cli, cliconfig, signup_service):
        result = cli.invoke(user_cli.add,
                            [u'--username', u'admin', u'--email', u'admin@localhost',
                             u'--password', u'admin', u'--authority', u'publisher.org'],
                            obj=cliconfig)

        assert result.exit_code == 0

        signup_service.signup.assert_called_with(username=u'admin',
                                                 email=u'admin@localhost',
                                                 password=u'admin',
                                                 authority=u'publisher.org',
                                                 require_activation=False)


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
    def admin_user(self, db_session, factories):
        return self._user(db_session, factories, True)

    @pytest.fixture
    def non_admin_user(self, db_session, factories):
        return self._user(db_session, factories, False)

    def _user(self, db_session, factories, admin):
        user = factories.User(admin=admin)
        db_session.flush()
        return user


@pytest.fixture
def signup_service():
    signup_service = mock.Mock(spec_set=['signup'])
    return signup_service


@pytest.fixture
def pyramid_config(pyramid_config, signup_service):
    pyramid_config.register_service(signup_service, name='user_signup')
    return pyramid_config


@pytest.fixture
def cliconfig(pyramid_config, pyramid_request):
    pyramid_request.tm = mock.Mock()
    return {'bootstrap': mock.Mock(return_value=pyramid_request)}
