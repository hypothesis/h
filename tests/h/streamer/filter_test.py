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
        ann_a = factories.Annotation(target_uri="https://example.com")
        ann_b = factories.Annotation(target_uri="https://example.net")

        query = {
            "match_policy": "include_any",
            "actions": {},
            "clauses": [{"field": "/id", "operator": "equals", "value": ann_a.id}],
        }
        handler = FilterHandler(query)

        assert handler.match(ann_a) is True
        assert handler.match(ann_b) is False

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
