# -*- coding: utf-8 -*-

import mock
import os
import pytest

from h.cli.commands import search
from h.search.client import Client


class TestReindexCommand(object):
    @pytest.mark.usefixtures("reindex")
    def test_it_raises_timeout(self, cli, cliconfig):
        cli.invoke(search.reindex, [], obj=cliconfig)
        assert os.getenv("ELASTICSEARCH_CLIENT_TIMEOUT") == "30"

    def test_calls_reindex(self, cli, cliconfig, pyramid_request, reindex):
        result = cli.invoke(search.reindex, [], obj=cliconfig)

        assert result.exit_code == 0
        reindex.assert_called_once_with(
            pyramid_request.db, pyramid_request.es, pyramid_request
        )

    @pytest.fixture
    def reindex(self, patch):
        index = patch("h.cli.commands.search.indexer")
        return index.reindex


class TestUpdateSettingsCommand(object):
    def test_calls_update_index_settings(
        self, cli, cliconfig, pyramid_request, update_index_settings
    ):
        result = cli.invoke(search.update_settings, [], obj=cliconfig)

        assert result.exit_code == 0
        update_index_settings.assert_called_once_with(pyramid_request.es)

    def test_handles_runtimeerror(self, cli, cliconfig, update_index_settings):
        update_index_settings.side_effect = RuntimeError("asplode!")

        result = cli.invoke(search.update_settings, [], obj=cliconfig)

        assert result.exit_code == 1
        assert "asplode!" in result.output

    @pytest.fixture
    def update_index_settings(self, patch):
        return patch("h.cli.commands.search.config.update_index_settings")


@pytest.fixture
def cliconfig(pyramid_request):
    pyramid_request.es = mock.create_autospec(Client, spec_set=True, instance=True)
    return {"bootstrap": mock.Mock(return_value=pyramid_request)}
