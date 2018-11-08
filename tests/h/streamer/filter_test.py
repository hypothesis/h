from __future__ import unicode_literals

from h.streamer.filter import FilterHandler


class TestFilterHandler(object):
    def test_it_matches_uri(self):
        query = {
            "match_policy": "include_any",
            "actions": {},
            "clauses": [
                {
                    "field": "/uri",
                    "operator": "one_of",
                    "value": ["https://example.com", "https://example.org"],
                }
            ],
        }
        handler = FilterHandler(query)

        ann = {"id": "123", "uri": "https://example.com"}
        assert handler.match(ann) is True

        ann = {"id": "123", "uri": "https://example.net"}
        assert handler.match(ann) is False

    def test_it_matches_id(self):
        query = {
            "match_policy": "include_any",
            "actions": {},
            "clauses": [
                {
                    "field": "/id",
                    "operator": "equals",
                    "value": "123",
                }
            ],
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
            "clauses": [
                {
                    "field": "/references",
                    "operator": "one_of",
                    "value": "123",
                }
            ],
        }
        handler = FilterHandler(query)

        ann = {"id": "abc", "uri": "https://example.com", "references": ["123"]}
        assert handler.match(ann) is True

        ann = {"id": "abc", "uri": "https://example.com", "references": ["456"]}
        assert handler.match(ann) is False
