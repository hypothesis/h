from datetime import datetime

import pytest

from h.streamer.filter import FilterHandler


class TestFilterHandler:
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
    def test_it_matches_uri(self, factories, query_uris, ann_uri, should_match):
        query = {
            "match_policy": "include_any",
            "actions": {},
            "clauses": [{"field": "/uri", "operator": "one_of", "value": query_uris}],
        }
        handler = FilterHandler(query)

        ann = factories.Annotation(target_uri=ann_uri)
        assert handler.match(ann) is should_match

    def test_it_matches_id(self, factories):
        ann_matching = factories.Annotation(target_uri="https://example.com")
        ann_non_matching = factories.Annotation(target_uri="https://example.net")

        query = {
            "match_policy": "include_any",
            "actions": {},
            "clauses": [
                {"field": "/id", "operator": "equals", "value": ann_matching.id}
            ],
        }
        handler = FilterHandler(query)

        assert handler.match(ann_matching) is True
        assert handler.match(ann_non_matching) is False

    def test_it_matches_parent_id(self, factories):
        parent_ann = factories.Annotation()
        other_ann = factories.Annotation()

        query = {
            "match_policy": "include_any",
            "actions": {},
            "clauses": [
                {"field": "/references", "operator": "one_of", "value": parent_ann.id}
            ],
        }
        handler = FilterHandler(query)

        ann = factories.Annotation(
            target_uri="https://example.com", references=[parent_ann.id]
        )
        assert handler.match(ann) is True

        ann = factories.Annotation(
            target_uri="https://example.com", references=[other_ann.id]
        )
        assert handler.match(ann) is False

    @pytest.mark.skip(reason="For dev purposes only")
    def test_speed(self, factories):  # pragma: no cover
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

        ann = factories.Annotation(target_uri="https://example.org")
        handler = FilterHandler(query)

        start = datetime.utcnow()

        # I think the max number connected at once is 4096
        for _ in range(4096):
            handler.match(ann)

        diff = datetime.utcnow() - start
        ms = diff.seconds * 1000 + diff.microseconds / 1000
        print(ms, "ms")
