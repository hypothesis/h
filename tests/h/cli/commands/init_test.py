
# -*- coding: utf-8 -*-

import mock
import pytest

from h.cli.commands import init as init_cli


@pytest.mark.usefixtures('db', 'search')
class TestInitCommand(object):
    def test_initialises_database(self,
                                  cli,
                                  cliconfig,
                                  db,
                                  db_engine,
                                  pyramid_settings):
        db.make_engine.return_value = db_engine
        pyramid_settings['h.authority'] = 'foobar.org'

        result = cli.invoke(init_cli.init, obj=cliconfig)

        db.make_engine.assert_called_once_with(pyramid_settings)
        db.init.assert_called_once_with(db_engine,
                                        should_create=True,
                                        authority='foobar.org')
        assert result.exit_code == 0

    def test_skips_database_init_if_alembic_managed(self,
                                                    request,
                                                    cli,
                                                    cliconfig,
                                                    db,
                                                    db_engine):
        db.make_engine.return_value = db_engine
        db_engine.execute('CREATE TABLE alembic_version (version_num VARCHAR(32));')

        @request.addfinalizer
        def _cleanup():
            db_engine.execute('DROP TABLE alembic_version;')

        result = cli.invoke(init_cli.init, obj=cliconfig)

        assert not db.init.called
        assert result.exit_code == 0

    def test_initialises_search(self,
                                cli,
                                cliconfig,
                                search,
                                pyramid_settings):
        client = search.get_client.return_value
        es6_client = search.get_es6_client.return_value

        result = cli.invoke(init_cli.init, obj=cliconfig)

        search.get_client.assert_called_once_with(pyramid_settings)
        search.init.assert_any_call(client)
        search.init.assert_any_call(es6_client)
        assert result.exit_code == 0


@pytest.fixture
def cliconfig(pyramid_request):
    return {'bootstrap': mock.Mock(return_value=pyramid_request)}


@pytest.fixture
def db(patch):
    return patch('h.cli.commands.init.db')


@pytest.fixture
def search(patch):
    return patch('h.cli.commands.init.search')
