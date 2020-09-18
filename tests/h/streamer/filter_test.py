from datetime import datetime
from random import random

import pytest
from h_matchers import Any

from h.streamer.filter import SocketFilter


class FakeSocket:
    ...


class TestFilterHandler:
    @pytest.mark.parametrize(
        "filter_uris,ann_uri,should_match",
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
    def test_it_matches_uri(
        self, factories, filter_uris, ann_uri, should_match, filter_matches
    ):
        ann = factories.Annotation(target_uri=ann_uri)

        filter_ = {
            "match_policy": "include_any",
            "actions": {},
            "clauses": [{"field": "/uri", "operator": "one_of", "value": filter_uris}],
        }

        assert filter_matches(filter_, ann) is should_match

    def test_it_matches_id(self, factories, filter_matches, annotation):
        other_annotation = factories.Annotation()

        filter_ = {
            "match_policy": "include_any",
            "actions": {},
            "clauses": [{"field": "/id", "operator": "equals", "value": annotation.id}],
        }

        assert filter_matches(filter_, annotation)
        assert not filter_matches(filter_, other_annotation)

    def test_it_does_not_crash_without_filter_rows(self, annotation):
        socket_no_rows = FakeSocket()

        result = tuple(SocketFilter.matching([socket_no_rows], annotation))
        assert not result

    def test_it_does_not_crash_with_unexpected_fields(self, annotation):
        socket = FakeSocket()
        socket.filter_rows = (("/not_a_thing", "value"),)

        result = tuple(SocketFilter.matching([socket], annotation))
        assert not result

    @pytest.mark.parametrize(
        "field,value,expected",
        (
            ("/id", "v1", [("/id", "v1")]),
            ("/references", "v1", [("/references", "v1")]),
            ("/uri", "v1", [("/uri", "v1")]),
            # Mapping
            ("/uri", "http://example.com", [("/uri", "httpx://example.com")]),
            # Multiple values
            ("/id", ["v1", "v2"], [("/id", "v1"), ("/id", "v2")]),
            ("/id", ["same", "same"], [("/id", "same")]),
            # Ignored
            ("/group", "v1", []),
            ("/random", "v1", []),
        ),
    )
    def test_set_filter(self, field, value, expected):
        socket = FakeSocket()

        filter_ = {
            "match_policy": "include_any",
            "actions": {},
            "clauses": [{"field": field, "operator": "one_of", "value": value}],
        }

        SocketFilter.set_filter(socket, filter_)

        assert socket.filter_rows == Any.iterable.containing(expected).only()

    def test_it_matches_parent_id(self, factories, filter_matches):
        parent_ann = factories.Annotation()
        other_ann = factories.Annotation()

        filter_ = {
            "match_policy": "include_any",
            "actions": {},
            "clauses": [
                {"field": "/references", "operator": "one_of", "value": parent_ann.id}
            ],
        }

        ann = factories.Annotation(
            target_uri="https://example.com", references=[parent_ann.id]
        )
        assert filter_matches(filter_, ann)

        ann = factories.Annotation(
            target_uri="https://example.com", references=[other_ann.id]
        )
        assert not filter_matches(filter_, ann)

    @pytest.mark.skip(reason="For dev purposes only")
    def test_speed(self, factories):  # pragma: no cover
        # I think the max number connected at once is 4096
        sockets = [FakeSocket() for _ in range(4096)]

        for socket in sockets:
            SocketFilter.set_filter(socket, self.get_randomized_filter())

        ann = factories.Annotation(target_uri="https://example.org")

        start = datetime.utcnow()
        # This returns a generator, we need to force it to produce answers
        tuple(SocketFilter.matching(sockets, ann))

        diff = datetime.utcnow() - start
        ms = diff.seconds * 1000 + diff.microseconds / 1000
        print(ms, "ms")

    def get_randomized_filter(self):
        return {
            "match_policy": "include_any",
            "actions": {},
            "clauses": [
                {
                    "field": "/id",
                    "operator": "equals",
                    "value": "3jgSANNlEeebpLMf36MACw" + str(random()),
                },
                {
                    "field": "/references",
                    "operator": "one_of",
                    "value": [
                        "3jgSANNlEeebpLMf36MACw" + str(random()),
                        "3jgSANNlEeebpLMf36MACw" + str(random()),
                    ],
                },
                {
                    "field": "/uri",
                    "operator": "one_of",
                    "value": [
                        "https://example.com",
                        "https://example.org" + str(random()),
                    ],
                },
            ],
        }

    @pytest.fixture
    def annotation(self, factories):
        return factories.Annotation()

    @pytest.fixture
    def filter_matches(self):
        def filter_matches(filter, annotation):
            socket = FakeSocket()
            SocketFilter.set_filter(socket, filter)

            return bool(tuple(SocketFilter.matching([socket], annotation)))

        return filter_matches
