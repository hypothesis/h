import os
from unittest import mock

import pytest

from h.cli.commands import search

pytestmark = [
    pytest.mark.xdist_group("elasticsearch"),
    pytest.mark.usefixtures("init_elasticsearch"),
]


class TestReindexCommand:
    @pytest.mark.usefixtures("reindex")
    def test_it_raises_timeout(self, cli, cliconfig):
        cli.invoke(search.reindex, [], obj=cliconfig)
        assert os.getenv("ELASTICSEARCH_CLIENT_TIMEOUT") == "30"

    def test_calls_reindex(self, cli, cliconfig, pyramid_request, reindex):
        result = cli.invoke(search.reindex, [], obj=cliconfig)

        assert not result.exit_code
        reindex.assert_called_once_with(
            pyramid_request.db, pyramid_request.es, pyramid_request
        )

    @pytest.fixture
    def reindex(self, patch):
        index = patch("h.cli.commands.search.indexer")
        return index.reindex


class TestUpdateSettingsCommand:
    def test_calls_update_index_settings(
        self, cli, cliconfig, pyramid_request, update_index_settings
    ):
        result = cli.invoke(search.update_settings, [], obj=cliconfig)

        assert not result.exit_code
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
def cliconfig(pyramid_request, mock_es_client):
    pyramid_request.es = mock_es_client
    return {"bootstrap": mock.Mock(return_value=pyramid_request)}
