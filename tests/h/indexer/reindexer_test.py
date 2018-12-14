# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import mock
import pytest

from h.indexer.reindexer import reindex
from h.search import client
from h.services.nipsa import NipsaService


@pytest.mark.usefixtures(
    "BatchIndexer",
    "configure_index",
    "delete_index",
    "nipsa_service",
    "get_aliased_index",
    "update_aliased_index",
    "settings_service",
)
class TestReindex(object):
    def test_sets_op_type_to_create(self, pyramid_request, es, BatchIndexer):
        reindex(mock.sentinel.session, es, pyramid_request)

        _, kwargs = BatchIndexer.call_args
        assert kwargs["op_type"] == "create"

    def test_indexes_annotations(self, pyramid_request, es, batchindexer):
        """Should call .index() on the batch indexer instance."""
        reindex(mock.sentinel.session, es, pyramid_request)

        batchindexer.index.assert_called_once_with()

    def test_retries_failed_annotations(self, pyramid_request, es, batchindexer):
        """Should call .index() a second time with any failed annotation IDs."""
        batchindexer.index.return_value = ["abc123", "def456"]

        reindex(mock.sentinel.session, es, pyramid_request)

        assert batchindexer.index.mock_calls == [
            mock.call(),
            mock.call(["abc123", "def456"]),
        ]

    def test_creates_new_index(self, pyramid_request, es, configure_index, matchers):
        """Creates a new target index."""
        reindex(mock.sentinel.session, es, pyramid_request)

        configure_index.assert_called_once_with(es)

    def test_passes_new_index_to_indexer(
        self, pyramid_request, es, configure_index, BatchIndexer
    ):
        """Pass the name of the new index as target_index to indexer."""
        configure_index.return_value = "hypothesis-abcd1234"

        reindex(mock.sentinel.session, es, pyramid_request)

        _, kwargs = BatchIndexer.call_args
        assert kwargs["target_index"] == "hypothesis-abcd1234"

    def test_updates_alias_when_reindexed(
        self, pyramid_request, es, configure_index, update_aliased_index
    ):
        """Call update_aliased_index on the client with the new index name."""
        configure_index.return_value = "hypothesis-abcd1234"

        reindex(mock.sentinel.session, es, pyramid_request)

        update_aliased_index.assert_called_once_with(es, "hypothesis-abcd1234")

    def test_does_not_update_alias_if_indexing_fails(
        self, pyramid_request, es, batchindexer, update_aliased_index
    ):
        """Don't call update_aliased_index if index() fails..."""
        batchindexer.index.side_effect = RuntimeError("fail")

        try:
            reindex(mock.sentinel.session, es, pyramid_request)
        except RuntimeError:
            pass

        assert not update_aliased_index.called

    def test_raises_if_index_not_aliased(self, es, get_aliased_index):
        get_aliased_index.return_value = None

        with pytest.raises(RuntimeError):
            reindex(mock.sentinel.session, es, mock.sentinel.request)

    def test_stores_new_index_name_in_settings(
        self, pyramid_request, es, settings_service, configure_index
    ):
        configure_index.return_value = "hypothesis-abcd1234"

        reindex(mock.sentinel.session, es, pyramid_request)

        settings_service.put.assert_called_once_with(
            "reindex.new_index", "hypothesis-abcd1234"
        )

    def test_deletes_index_name_setting(self, pyramid_request, es, settings_service):
        reindex(mock.sentinel.session, es, pyramid_request)

        settings_service.delete.assert_called_once_with("reindex.new_index")

    def test_deletes_index_name_setting_when_exception_raised(
        self, pyramid_request, es, settings_service, batchindexer
    ):
        batchindexer.index.side_effect = RuntimeError("boom!")

        with pytest.raises(RuntimeError):
            reindex(mock.sentinel.session, es, pyramid_request)

        settings_service.delete.assert_called_once_with("reindex.new_index")

    def test_deletes_old_index(
        self, pyramid_request, es, delete_index, get_aliased_index
    ):
        get_aliased_index.return_value = "original_index"

        reindex(mock.sentinel.session, es, pyramid_request)

        delete_index.assert_called_once_with(es, "original_index")

    def test_populates_nipsa_cache(self, pyramid_request, es, nipsa_service):
        reindex(mock.sentinel.session, es, pyramid_request)
        nipsa_service.fetch_all_flagged_userids.assert_called_once_with()

    @pytest.fixture
    def BatchIndexer(self, patch):
        return patch("h.indexer.reindexer.BatchIndexer")

    @pytest.fixture
    def configure_index(self, patch):
        return patch("h.indexer.reindexer.configure_index")

    @pytest.fixture
    def get_aliased_index(self, patch):
        func = patch("h.indexer.reindexer.get_aliased_index")
        func.return_value = "foobar"
        return func

    @pytest.fixture
    def delete_index(self, patch):
        return patch("h.indexer.reindexer.delete_index")

    @pytest.fixture
    def update_aliased_index(self, patch):
        return patch("h.indexer.reindexer.update_aliased_index")

    @pytest.fixture
    def batchindexer(self, BatchIndexer):
        indexer = BatchIndexer.return_value
        indexer.index.return_value = []
        return indexer

    @pytest.fixture
    def es(self):
        mock_es = mock.create_autospec(
            client.Client,
            instance=True,
            spec_set=True,
            index="hypothesis",
            version=(1, 5, 0),
        )
        mock_es.mapping_type = "annotation"
        return mock_es

    @pytest.fixture
    def settings_service(self, pyramid_config):
        service = mock.Mock()
        pyramid_config.register_service(service, name="settings")
        return service

    @pytest.fixture
    def nipsa_service(self, pyramid_config):
        service = mock.create_autospec(NipsaService, spec_set=True, instance=True)
        pyramid_config.register_service(service, name="nipsa")
        return service

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.tm = mock.Mock()
        return pyramid_request
