import itertools
import re
from unittest.mock import MagicMock
from urllib.parse import quote_plus

import elasticsearch
import pytest
from h_matchers import Any
from packaging.version import Version

from h.search.config import (
    ANALYSIS_SETTINGS,
    ANNOTATION_MAPPING,
    configure_index,
    delete_index,
    get_aliased_index,
    init,
    update_aliased_index,
    update_index_settings,
)

pytestmark = [
    pytest.mark.xdist_group("elasticsearch"),
    pytest.mark.usefixtures("init_elasticsearch"),
]


def test_strip_scheme_char_filter():
    f = ANALYSIS_SETTINGS["char_filter"]["strip_scheme"]
    p = f["pattern"]
    r = f["replacement"]
    assert re.sub(p, r, "http://ping/pong#hash") == "ping/pong#hash"
    assert re.sub(p, r, "chrome-extension://1234/a.js") == "1234/a.js"
    assert re.sub(p, r, "a+b.c://1234/a.js") == "1234/a.js"
    assert re.sub(p, r, "uri:x-pdf:1234") == "x-pdf:1234"
    assert re.sub(p, r, "example.com") == "example.com"
    # This is ambiguous, and possibly cannot be expected to work.
    # assert(re.sub(p, r, 'localhost:5000') == 'localhost:5000')


def test_path_url_filter():
    patterns = ANALYSIS_SETTINGS["filter"]["path_url"]["patterns"]
    assert captures(patterns, "example.com/foo/bar?query#hash") == [
        "example.com/foo/bar"
    ]
    assert captures(patterns, "example.com/foo/bar/") == ["example.com/foo/bar/"]


def test_rstrip_slash_filter():
    p = ANALYSIS_SETTINGS["filter"]["rstrip_slash"]["pattern"]
    r = ANALYSIS_SETTINGS["filter"]["rstrip_slash"]["replacement"]
    assert re.sub(p, r, "example.com/") == "example.com"
    assert re.sub(p, r, "example.com/foo/bar/") == "example.com/foo/bar"


def test_uri_part_tokenizer():
    text = "http://a.b/foo/bar?c=d#stuff"
    pattern = ANALYSIS_SETTINGS["tokenizer"]["uri_part"]["pattern"]
    assert re.split(pattern, text) == [
        "http",
        "",
        "",
        "a",
        "b",
        "foo",
        "bar",
        "c",
        "d",
        "stuff",
    ]

    text = quote_plus(text)
    assert re.split(pattern, "http://jump.to/?u=" + text) == [
        "http",
        "",
        "",
        "jump",
        "to",
        "",
        "u",
        "http",
        "",
        "",
        "a",
        "b",
        "foo",
        "bar",
        "c",
        "d",
        "stuff",
    ]


@pytest.mark.usefixtures("mock_es_client", "configure_index")
class TestInit:
    def test_configures_index_when_index_missing(self, mock_es_client, configure_index):
        """Calls configure_index when one doesn't exist."""
        init(mock_es_client)

        configure_index.assert_called_once_with(mock_es_client)

    def test_configures_alias(self, mock_es_client):
        """Adds an alias to the newly-created index."""
        init(mock_es_client)

        mock_es_client.conn.indices.put_alias.assert_called_once_with(
            index="foo-abcd1234", name=mock_es_client.index
        )

    def test_does_not_recreate_extant_index(self, mock_es_client, configure_index):
        """Exits early if the index (or an alias) already exists."""
        mock_es_client.conn.indices.exists.return_value = True

        init(mock_es_client)

        assert not configure_index.called

    def test_raises_if_icu_analysis_plugin_unavailable(self, mock_es_client):
        mock_es_client.conn.cat.plugins.return_value = ""

        with pytest.raises(RuntimeError) as e:
            init(mock_es_client)

        assert "plugin is not installed" in str(e.value)

    def test_skips_plugin_check(self, mock_es_client, configure_index):
        mock_es_client.conn.cat.plugins.return_value = ""

        init(mock_es_client, check_icu_plugin=False)

        configure_index.assert_called_once_with(mock_es_client)

    @pytest.fixture
    def mock_es_client(self, mock_es_client):
        # By default, pretend that no index exists already...
        mock_es_client.conn.indices.exists.return_value = False
        # Simulate the ICU Analysis plugin, and get around some funky stuff
        # the ES client library does which confuses autospeccing
        mock_es_client.conn.cat.plugins = MagicMock()
        mock_es_client.conn.cat.plugins.return_value = "\n".join(
            ["foo", "analysis-icu"]
        )
        return mock_es_client

    @pytest.fixture
    def configure_index(self, patch):
        configure_index = patch("h.search.config.configure_index")
        configure_index.return_value = "foo-abcd1234"
        return configure_index


class TestConfigureIndex:
    def test_creates_randomly_named_index(self, mock_es_client):
        configure_index(mock_es_client)

        mock_es_client.conn.indices.create.assert_called_once_with(
            Any.string.matching(mock_es_client.index + "-[0-9a-f]{8}"), body=Any()
        )

    def test_returns_index_name(self, mock_es_client):
        name = configure_index(mock_es_client)

        assert name == Any.string.matching(mock_es_client.index + "-[0-9a-f]{8}")

    def test_sets_correct_mappings_and_settings(self, mock_es_client):
        configure_index(mock_es_client)

        mock_es_client.conn.indices.create.assert_called_once_with(
            Any(),
            body={
                "mappings": {"annotation": ANNOTATION_MAPPING},
                "settings": {"analysis": ANALYSIS_SETTINGS},
            },
        )

    def test_sets_correct_mappings_and_settings_for_es7(self, mock_es_client):
        mock_es_client.mapping_type = "_doc"
        mock_es_client.server_version = Version("7.10.0")

        configure_index(mock_es_client)

        mock_es_client.conn.indices.create.assert_called_once_with(
            Any(),
            body={
                "mappings": ANNOTATION_MAPPING,
                "settings": {"analysis": ANALYSIS_SETTINGS},
            },
        )


class TestGetAliasedIndex:
    def test_returns_underlying_index_name(self, mock_es_client):
        """If ``index`` is an alias, return the name of the concrete index."""
        mock_es_client.conn.indices.get_alias.return_value = {
            "target-index": {"aliases": {"foo": {}}}
        }

        assert get_aliased_index(mock_es_client) == "target-index"

    def test_returns_none_when_no_alias(self, mock_es_client):
        """If ``index`` is a concrete index, return None."""
        mock_es_client.conn.indices.get_alias.side_effect = (
            elasticsearch.exceptions.NotFoundError("test", "test desc")
        )

        assert get_aliased_index(mock_es_client) is None

    def test_raises_if_aliased_to_multiple_indices(self, mock_es_client):
        """Raise if ``index`` is an alias pointing to multiple indices."""
        mock_es_client.conn.indices.get_alias.return_value = {
            "index-one": {"aliases": {"foo": {}}},
            "index-two": {"aliases": {"foo": {}}},
        }

        with pytest.raises(RuntimeError):
            get_aliased_index(mock_es_client)


class TestUpdateAliasedIndex:
    def test_updates_index_atomically(self, mock_es_client):
        """Update the alias atomically."""
        mock_es_client.conn.indices.get_alias.return_value = {
            "old-target": {"aliases": {mock_es_client.index: {}}}
        }

        update_aliased_index(mock_es_client, "new-target")
        mock_es_client.conn.indices.update_aliases.assert_called_once_with(
            body={
                "actions": [
                    {"add": {"index": "new-target", "alias": mock_es_client.index}},
                    {"remove": {"index": "old-target", "alias": mock_es_client.index}},
                ]
            }
        )

    def test_raises_if_called_for_concrete_index(self, mock_es_client):
        """Raise if called for a concrete index."""
        mock_es_client.conn.indices.get_alias.side_effect = (
            elasticsearch.exceptions.NotFoundError("test", "test desc")
        )

        with pytest.raises(RuntimeError):
            update_aliased_index(mock_es_client, "new-target")


class TestDeleteIndex:
    def test_deletes_index(self, mock_es_client):
        delete_index(mock_es_client, "unused-index")

        mock_es_client.conn.indices.delete.assert_called_once_with(index="unused-index")


class TestUpdateIndexSettings:
    def test_succesfully_updates_the_index_settings(self, mock_es_client):
        mock_es_client.conn.indices.get_alias.return_value = {
            "old-target": {"aliases": {"foo": {}}}
        }
        mock_es_client.conn.indices.get_settings.return_value = {
            "old-target": {"settings": {"index": {"analysis": {"old_setting": "val"}}}}
        }

        update_index_settings(mock_es_client)

        mock_es_client.conn.indices.put_settings.assert_called_once_with(
            index="old-target", body={"analysis": ANALYSIS_SETTINGS}
        )
        mock_es_client.conn.indices.put_mapping.assert_called_once_with(
            index="old-target",
            doc_type=mock_es_client.mapping_type,
            body=ANNOTATION_MAPPING,
        )

    def test_raises_original_exception_if_not_merge_mapping_exception(
        self, mock_es_client
    ):
        mock_es_client.conn.indices.get_alias.return_value = {
            "old-target": {"aliases": {"foo": {}}}
        }
        error = elasticsearch.exceptions.RequestError
        mock_es_client.conn.indices.put_mapping.side_effect = error("test", "test desc")

        with pytest.raises(error):
            update_index_settings(mock_es_client)

    def test_raises_runtime_exception_if_merge_mapping_exception(self, mock_es_client):
        mock_es_client.conn.indices.get_alias.return_value = {
            "old-target": {"aliases": {"foo": {}}}
        }
        mock_es_client.conn.indices.put_mapping.side_effect = (
            elasticsearch.exceptions.RequestError("test", "MergeMappingException")
        )

        with pytest.raises(RuntimeError):
            update_index_settings(mock_es_client)


def captures(patterns, text):
    return list(itertools.chain(*(groups(p, text) for p in patterns)))


def groups(pattern, text):
    return re.search(pattern, text).groups() or []
