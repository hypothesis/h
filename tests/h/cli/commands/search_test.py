# -*- coding: utf-8 -*-

import mock
import pytest

from h.cli.commands import search


class TestReindexCommand(object):
    def test_calls_reindex(self, cli, cliconfig, pyramid_request, reindex):
        result = cli.invoke(search.reindex, [], obj=cliconfig)

        assert result.exit_code == 0
        reindex.assert_called_once_with(pyramid_request.db,
                                        pyramid_request.es,
                                        pyramid_request)

    @pytest.fixture
    def cliconfig(self, pyramid_request):
        pyramid_request.es = mock.sentinel.es
        return {'bootstrap': mock.Mock(return_value=pyramid_request)}

    @pytest.fixture
    def reindex(self, patch):
        index = patch('h.cli.commands.search.index')
        return index.reindex
