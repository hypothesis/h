import logging
from unittest.mock import sentinel

import pytest
from sqlalchemy.exc import ProgrammingError

from h.cli.commands.init import init


class TestInitCommand:
    def test_it_overrides_the_elasticsearch_client_timeout(self, cli, ctx, os):
        result = cli.invoke(init, obj=ctx)

        assert os.environ["ELASTICSEARCH_CLIENT_TIMEOUT"] == "30"
        assert not result.exit_code

    def test_it_initializes_the_db(
        self, alembic, caplog, cli, ctx, db, db_engine, pyramid_request
    ):
        caplog.set_level(logging.INFO)
        db_engine.execute.side_effect = ProgrammingError(
            sentinel.statement, sentinel.params, sentinel.orig
        )

        result = cli.invoke(init, obj=ctx)

        db.make_engine.assert_called_once_with(pyramid_request.registry.settings)
        db_engine.execute.assert_called_once_with("select 1 from alembic_version")
        assert (
            "h.cli.commands.init",
            logging.INFO,
            "initializing database",
        ) in caplog.record_tuples
        db.init.assert_called_once_with(
            db_engine,
            should_create=True,
            authority=pyramid_request.registry.settings["h.authority"],
        )
        alembic.config.Config.assert_called_once_with("conf/alembic.ini")
        alembic.command.stamp.assert_called_once_with(
            alembic.config.Config.return_value, "head"
        )
        assert not result.exit_code

    def test_it_skips_initializing_the_db_if_its_already_initialized(
        self, alembic, caplog, cli, ctx, db
    ):
        caplog.set_level(logging.INFO)

        result = cli.invoke(init, obj=ctx)

        db.init.assert_not_called()
        alembic.command.stamp.assert_not_called()
        assert (
            "h.cli.commands.init",
            logging.INFO,
            "detected alembic_version table, skipping db initialization",
        ) in caplog.record_tuples
        assert not result.exit_code

    @pytest.mark.parametrize(
        "settings,check_icu_plugin",
        [
            ({"es.check_icu_plugin": True}, True),
            ({"es.check_icu_plugin": False}, False),
            ({}, True),
        ],
    )
    def test_it_initializes_elasticsearch(
        self, caplog, cli, ctx, search, pyramid_request, settings, check_icu_plugin
    ):
        caplog.set_level(logging.INFO)
        pyramid_request.registry.settings.update(settings)

        result = cli.invoke(init, obj=ctx)

        search.get_client.assert_called_once_with(pyramid_request.registry.settings)
        assert (
            "h.cli.commands.init",
            logging.INFO,
            "initializing ES6 search index",
        ) in caplog.record_tuples
        search.init.assert_called_once_with(
            search.get_client.return_value, check_icu_plugin=check_icu_plugin
        )
        assert not result.exit_code


@pytest.fixture(autouse=True)
def os(patch):
    os = patch("h.cli.commands.init.os")
    os.environ = {}
    return os


@pytest.fixture(autouse=True)
def alembic(patch):
    return patch("h.cli.commands.init.alembic")


@pytest.fixture(autouse=True)
def db(patch):
    return patch("h.cli.commands.init.db")


@pytest.fixture(autouse=True)
def search(patch):
    return patch("h.cli.commands.init.search")


@pytest.fixture(autouse=True)
def pyramid_settings(pyramid_settings):
    pyramid_settings["h.authority"] = sentinel.h_authority
    return pyramid_settings


@pytest.fixture
def ctx(pyramid_request):
    return {"bootstrap": lambda: pyramid_request}


@pytest.fixture
def db_engine(db):
    return db.make_engine.return_value
