from unittest import mock

import pytest

from h.cli.commands import init as init_cli


@pytest.mark.usefixtures("alembic_config", "alembic_stamp", "db", "search")
class TestInitCommand:
    def test_initialises_database(
        self, cli, cliconfig, db, db_engine, pyramid_settings
    ):
        db.make_engine.return_value = db_engine
        pyramid_settings["h.authority"] = "foobar.org"

        result = cli.invoke(init_cli.init, obj=cliconfig)

        db.make_engine.assert_called_once_with(pyramid_settings)
        db.init.assert_called_once_with(
            db_engine, should_create=True, authority="foobar.org"
        )
        assert not result.exit_code

    def test_skips_database_init_if_alembic_managed(
        self, request, cli, cliconfig, db, db_engine
    ):
        db.make_engine.return_value = db_engine
        db_engine.execute("CREATE TABLE alembic_version (version_num VARCHAR(32));")

        @request.addfinalizer
        def _cleanup():
            db_engine.execute("DROP TABLE alembic_version;")

        result = cli.invoke(init_cli.init, obj=cliconfig)

        assert not db.init.called
        assert not result.exit_code

    def test_stamps_alembic_version(
        self,
        alembic_config,
        alembic_stamp,
        cli,
        cliconfig,
        db,
        db_engine,
        pyramid_settings,
    ):
        db.make_engine.return_value = db_engine
        Config = alembic_config.Config
        pyramid_settings["h.authority"] = "foobar.org"

        result = cli.invoke(init_cli.init, obj=cliconfig)

        Config.assert_called_once_with("conf/alembic.ini")
        alembic_stamp.assert_called_once_with(Config.return_value, "head")
        assert not result.exit_code

    def test_initialises_search(self, cli, cliconfig, search, pyramid_settings):
        pyramid_settings["es.check_icu_plugin"] = False
        es_client = search.get_client.return_value
        result = cli.invoke(init_cli.init, obj=cliconfig)

        search.get_client.assert_called_once_with(pyramid_settings)
        search.init.assert_any_call(es_client, pyramid_settings["es.check_icu_plugin"])
        assert not result.exit_code


@pytest.fixture
def cliconfig(pyramid_request):
    return {"bootstrap": mock.Mock(return_value=pyramid_request)}


@pytest.fixture
def db(patch):
    return patch("h.cli.commands.init.db")


@pytest.fixture
def search(patch):
    return patch("h.cli.commands.init.search")


@pytest.fixture
def alembic_config(patch):
    return patch("h.cli.commands.init.alembic.config")


@pytest.fixture
def alembic_stamp(patch):
    return patch("h.cli.commands.init.alembic.command.stamp")
