# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from h._compat import url_quote_plus

import itertools
import re

import mock
import pytest
import elasticsearch

from h.search.client import Client
from h.search.config import (
    ANNOTATION_MAPPING,
    ANALYSIS_SETTINGS,
    init,
    configure_index,
    delete_index,
    get_aliased_index,
    update_aliased_index,
    update_index_settings,
)


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

    text = url_quote_plus(text)
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


@pytest.mark.usefixtures("client", "configure_index")
class TestInit(object):
    def test_configures_index_when_index_missing(self, client, configure_index):
        """Calls configure_index when one doesn't exist."""
        init(client)

        configure_index.assert_called_once_with(client)

    def test_configures_alias(self, client):
        """Adds an alias to the newly-created index."""
        init(client)

        client.conn.indices.put_alias.assert_called_once_with(
            index="foo-abcd1234", name="foo"
        )

    def test_does_not_recreate_extant_index(self, client, configure_index):
        """Exits early if the index (or an alias) already exists."""
        client.conn.indices.exists.return_value = True

        init(client)

        assert not configure_index.called

    def test_raises_if_icu_analysis_plugin_unavailable(self, client):
        client.conn.cat.plugins.return_value = ""

        with pytest.raises(RuntimeError) as e:
            init(client)

        assert "plugin is not installed" in str(e.value)

    def test_skips_plugin_check(self, client, configure_index):
        client.conn.cat.plugins.return_value = ""

        init(client, check_icu_plugin=False)

        configure_index.assert_called_once_with(client)

    @pytest.fixture
    def client(self, client):
        # By default, pretend that no index exists already...
        client.conn.indices.exists.return_value = False
        # Simulate the ICU Analysis plugin
        client.conn.cat.plugins.return_value = "\n".join(["foo", "analysis-icu"])
        return client

    @pytest.fixture
    def configure_index(self, patch):
        configure_index = patch("h.search.config.configure_index")
        configure_index.return_value = "foo-abcd1234"
        return configure_index


class TestConfigureIndex(object):
    def test_creates_randomly_named_index(self, client, matchers):
        configure_index(client)

        client.conn.indices.create.assert_called_once_with(
            matchers.Regex("foo-[0-9a-f]{8}"), body=mock.ANY
        )

    def test_returns_index_name(self, client, matchers):
        name = configure_index(client)

        assert name == matchers.Regex("foo-[0-9a-f]{8}")

    def test_sets_correct_mappings_and_settings(self, client):
        configure_index(client)

        client.conn.indices.create.assert_called_once_with(
            mock.ANY,
            body={
                "mappings": {"annotation": ANNOTATION_MAPPING},
                "settings": {"analysis": ANALYSIS_SETTINGS},
            },
        )


class TestGetAliasedIndex(object):
    def test_returns_underlying_index_name(self, client):
        """If ``index`` is an alias, return the name of the concrete index."""
        client.conn.indices.get_alias.return_value = {
            "target-index": {"aliases": {"foo": {}}}
        }

        assert get_aliased_index(client) == "target-index"

    def test_returns_none_when_no_alias(self, client):
        """If ``index`` is a concrete index, return None."""
        client.conn.indices.get_alias.side_effect = elasticsearch.exceptions.NotFoundError(
            "test", "test desc"
        )

        assert get_aliased_index(client) is None

    def test_raises_if_aliased_to_multiple_indices(self, client):
        """Raise if ``index`` is an alias pointing to multiple indices."""
        client.conn.indices.get_alias.return_value = {
            "index-one": {"aliases": {"foo": {}}},
            "index-two": {"aliases": {"foo": {}}},
        }

        with pytest.raises(RuntimeError):
            get_aliased_index(client)


class TestUpdateAliasedIndex(object):
    def test_updates_index_atomically(self, client):
        """Update the alias atomically."""
        client.conn.indices.get_alias.return_value = {
            "old-target": {"aliases": {"foo": {}}}
        }

        update_aliased_index(client, "new-target")
        client.conn.indices.update_aliases.assert_called_once_with(
            body={
                "actions": [
                    {"add": {"index": "new-target", "alias": "foo"}},
                    {"remove": {"index": "old-target", "alias": "foo"}},
                ]
            }
        )

    def test_raises_if_called_for_concrete_index(self, client):
        """Raise if called for a concrete index."""
        client.conn.indices.get_alias.side_effect = elasticsearch.exceptions.NotFoundError(
            "test", "test desc"
        )

        with pytest.raises(RuntimeError):
            update_aliased_index(client, "new-target")


class TestDeleteIndex(object):
    def test_deletes_index(self, client):
        delete_index(client, "unused-index")

        client.conn.indices.delete.assert_called_once_with(index="unused-index")


class TestUpdateIndexSettings(object):
    def test_succesfully_updates_the_index_settings(self, client):
        client.conn.indices.get_alias.return_value = {
            "old-target": {"aliases": {"foo": {}}}
        }
        client.conn.indices.get_settings.return_value = {
            "old-target": {"settings": {"index": {"analysis": {"old_setting": "val"}}}}
        }

        update_index_settings(client)

        client.conn.indices.put_settings.assert_called_once_with(
            index="old-target", body={"analysis": ANALYSIS_SETTINGS}
        )
        client.conn.indices.put_mapping.assert_called_once_with(
            index="old-target", doc_type=client.mapping_type, body=ANNOTATION_MAPPING
        )

    def test_raises_original_exception_if_not_merge_mapping_exception(self, client):
        client.conn.indices.get_alias.return_value = {
            "old-target": {"aliases": {"foo": {}}}
        }
        error = elasticsearch.exceptions.RequestError
        client.conn.indices.put_mapping.side_effect = error("test", "test desc")

        with pytest.raises(error):
            update_index_settings(client)

    def test_raises_runtime_exception_if_merge_mapping_exception(self, client):
        client.conn.indices.get_alias.return_value = {
            "old-target": {"aliases": {"foo": {}}}
        }
        client.conn.indices.put_mapping.side_effect = elasticsearch.exceptions.RequestError(
            "test", "MergeMappingException"
        )

        with pytest.raises(RuntimeError):
            update_index_settings(client)


def captures(patterns, text):
    return list(itertools.chain(*(groups(p, text) for p in patterns)))


def groups(pattern, text):
    return re.search(pattern, text).groups() or []


@pytest.fixture
def client():
    client = mock.create_autospec(
        Client, spec_set=True, instance=True, version=elasticsearch.__version__
    )
    client.index = "foo"
    client.mapping_type = "annotation"
    return client
