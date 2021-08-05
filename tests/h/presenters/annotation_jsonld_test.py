import datetime

import pytest
from h_matchers import Any

from h.presenters.annotation_jsonld import AnnotationJSONLDPresenter


class TestAnnotationJSONLDPresenter:
    def test_it(self, presenter, annotation, links_service):
        annotation.created = datetime.datetime(2016, 2, 24, 18, 3, 25, 768)
        annotation.updated = datetime.datetime(2016, 2, 29, 10, 24, 5, 564)

        expected = {
            "@context": "http://www.w3.org/ns/anno.jsonld",
            "type": "Annotation",
            "id": links_service.get.return_value,
            "created": "2016-02-24T18:03:25.000768+00:00",
            "modified": "2016-02-29T10:24:05.000564+00:00",
            "creator": annotation.userid,
            "body": Any.list(),
            "target": [
                {
                    "source": annotation.target_uri,
                    "selector": Any.list(),
                }
            ],
        }

        result = presenter.asdict()

        assert result == expected

    def test_it_returns_bodies(self, presenter, annotation):
        result = presenter.asdict()

        expected_bodies = [
            {
                "type": "TextualBody",
                "format": "text/markdown",
                "value": annotation.text,
            }
        ]
        expected_bodies.extend(
            [
                {"type": "TextualBody", "value": tag, "purpose": "tagging"}
                for tag in annotation.tags
            ]
        )
        assert result["body"] == expected_bodies

    def test_it_ignores_selectors_lacking_types(self, presenter, annotation):
        annotation.target_selectors = [
            {"type": "TestSelector", "test": "foobar"},
            {"something": "else"},
        ]

        result = presenter.asdict()

        assert result["target"][0]["selector"] == [
            {"type": "TestSelector", "test": "foobar"}
        ]

    def test_rewrites_rangeselectors_same_element(self, presenter, annotation):
        # A RangeSelector that starts and ends in the same element should be
        # rewritten to an XPathSelector refinedBy a TextPositionSelector, for
        # the sake of simplicity.
        annotation.target_selectors = [
            {
                "type": "RangeSelector",
                "startContainer": "/div[1]/main[1]/article[1]/div[2]/p[339]",
                "startOffset": 12,
                "endContainer": "/div[1]/main[1]/article[1]/div[2]/p[339]",
                "endOffset": 43,
            }
        ]

        result = presenter.asdict()

        assert result["target"][0]["selector"] == [
            {
                "type": "XPathSelector",
                "value": "/div[1]/main[1]/article[1]/div[2]/p[339]",
                "refinedBy": {"type": "TextPositionSelector", "start": 12, "end": 43},
            }
        ]

    def test_rewrites_rangeselectors_different_element(self, presenter, annotation):
        # A RangeSelector that starts and ends in the different elements should
        # be rewritten to a RangeSelector bounded by two XPathSelectors, each of
        # which is refinedBy a "point"-like TextPositionSelector.
        annotation.target_selectors = [
            {
                "type": "RangeSelector",
                "startContainer": "/div[1]/main[1]/article[1]/div[2]/h1[1]",
                "startOffset": 4,
                "endContainer": "/div[1]/main[1]/article[1]/div[2]/p[339]",
                "endOffset": 72,
            }
        ]

        result = presenter.asdict()

        assert result["target"][0]["selector"] == [
            {
                "type": "RangeSelector",
                "startSelector": {
                    "type": "XPathSelector",
                    "value": "/div[1]/main[1]/article[1]/div[2]/h1[1]",
                    "refinedBy": {"type": "TextPositionSelector", "start": 4, "end": 4},
                },
                "endSelector": {
                    "type": "XPathSelector",
                    "value": "/div[1]/main[1]/article[1]/div[2]/p[339]",
                    "refinedBy": {
                        "type": "TextPositionSelector",
                        "start": 72,
                        "end": 72,
                    },
                },
            }
        ]

    def test_ignores_malformed_rangeselectors(self, presenter, annotation):
        annotation.target_selectors = [
            {
                "type": "RangeSelector",
                "startContainer": "/div[1]/main[1]/article[1]/div[2]/h1[1]",
                "startOffset": 4,
                "endContainer": "/div[1]/main[1]/article[1]/div[2]/p[339]",
            }
        ]

        result = presenter.asdict()

        assert "selector" not in result["target"][0]

    @pytest.fixture
    def annotation(self, factories):
        return factories.Annotation.build()

    @pytest.fixture
    def presenter(self, annotation, links_service):
        return AnnotationJSONLDPresenter(annotation, links_service)
