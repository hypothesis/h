from __future__ import unicode_literals

import pytest

from h.streamer.filter import FilterHandler


class TestFilterHandler(object):
    @pytest.mark.parametrize(
        "query_uris,ann_uri,should_match",
        [
            # Test cases that require only exact comparisons.
            (
                ["https://example.com", "https://example.org"],
                "https://example.com",
                True,
            ),
            (
                ["https://example.com", "https://example.org"],
                "https://example.net",
                False,
            ),
            # Test cases that require comparison of normalized URIs.
            (["https://example.com"], "http://example.com", True),
            (["http://example.com"], "https://example.com", True),
            (["http://example.com/?"], "https://example.com", True),
            (["http://example.com"], "https://example.com/?", True),
        ],
    )
    def test_it_matches_uri(self, query_uris, ann_uri, should_match):
        query = {
            "match_policy": "include_any",
            "actions": {},
            "clauses": [{"field": "/uri", "operator": "one_of", "value": query_uris}],
        }
        handler = FilterHandler(query)

        ann = {"id": "123", "uri": ann_uri}
        assert handler.match(ann) is should_match

    def test_it_matches_id(self):
        query = {
            "match_policy": "include_any",
            "actions": {},
            "clauses": [{"field": "/id", "operator": "equals", "value": "123"}],
        }
        handler = FilterHandler(query)

        ann = {"id": "123", "uri": "https://example.com"}
        assert handler.match(ann) is True

        ann = {"id": "456", "uri": "https://example.net"}
        assert handler.match(ann) is False

    def test_it_matches_parent_id(self):
        query = {
            "match_policy": "include_any",
            "actions": {},
            "clauses": [{"field": "/references", "operator": "one_of", "value": "123"}],
        }
        handler = FilterHandler(query)

        ann = {"id": "abc", "uri": "https://example.com", "references": ["123"]}
        assert handler.match(ann) is True

        ann = {"id": "abc", "uri": "https://example.com", "references": ["456"]}
        assert handler.match(ann) is False
