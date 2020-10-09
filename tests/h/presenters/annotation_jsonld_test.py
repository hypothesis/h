import datetime
from unittest import mock

from h_matchers import Any

from h.presenters.annotation_jsonld import AnnotationJSONLDPresenter
from h.traversal import AnnotationContext


class TestAnnotationJSONLDPresenter:
    def test_asdict(self, groupfinder_service, links_service):
        annotation = mock.Mock(
            id="foobar",
            created=datetime.datetime(2016, 2, 24, 18, 3, 25, 768),
            updated=datetime.datetime(2016, 2, 29, 10, 24, 5, 564),
            userid="acct:luke",
            target_uri="http://example.com",
            text="It is magical!",
            tags=["magic"],
            target_selectors=[{"type": "TestSelector", "test": "foobar"}],
        )
        expected = {
            "@context": "http://www.w3.org/ns/anno.jsonld",
            "type": "Annotation",
            "id": links_service.get.return_value,
            "created": "2016-02-24T18:03:25.000768+00:00",
            "modified": "2016-02-29T10:24:05.000564+00:00",
            "creator": "acct:luke",
            "body": [
                {
                    "type": "TextualBody",
                    "format": "text/markdown",
                    "value": "It is magical!",
                },
                {"type": "TextualBody", "purpose": "tagging", "value": "magic"},
            ],
            "target": [
                {
                    "source": "http://example.com",
                    "selector": [{"type": "TestSelector", "test": "foobar"}],
                }
            ],
        }

        resource = AnnotationContext(annotation, groupfinder_service, links_service)
        result = AnnotationJSONLDPresenter(resource).asdict()

        assert result == expected

    def test_id_returns_jsonld_id_link(self, groupfinder_service, links_service):
        annotation = mock.Mock(id="foobar")
        resource = AnnotationContext(annotation, groupfinder_service, links_service)
        presenter = AnnotationJSONLDPresenter(resource)

        result = presenter.id

        assert result == links_service.get.return_value
        links_service.get.assert_called_once_with(annotation, Any())

    def test_bodies_returns_textual_body(self, groupfinder_service, links_service):
        annotation = mock.Mock(text="Flib flob flab", tags=None)
        resource = AnnotationContext(annotation, groupfinder_service, links_service)

        bodies = AnnotationJSONLDPresenter(resource).bodies

        assert bodies == [
            {
                "type": "TextualBody",
                "value": "Flib flob flab",
                "format": "text/markdown",
            }
        ]

    def test_bodies_appends_tag_bodies(self, groupfinder_service, links_service):
        annotation = mock.Mock(text="Flib flob flab", tags=["giraffe", "lion"])
        resource = AnnotationContext(annotation, groupfinder_service, links_service)

        bodies = AnnotationJSONLDPresenter(resource).bodies

        assert {
            "type": "TextualBody",
            "value": "giraffe",
            "purpose": "tagging",
        } in bodies
        assert {"type": "TextualBody", "value": "lion", "purpose": "tagging"} in bodies

    def test_ignores_selectors_lacking_types(self, groupfinder_service, links_service):
        annotation = mock.Mock(target_uri="http://example.com")
        annotation.target_selectors = [
            {"type": "TestSelector", "test": "foobar"},
            {"something": "else"},
        ]
        resource = AnnotationContext(annotation, groupfinder_service, links_service)

        selectors = AnnotationJSONLDPresenter(resource).target[0]["selector"]

        assert selectors == [{"type": "TestSelector", "test": "foobar"}]

    def test_rewrites_rangeselectors_same_element(
        self, groupfinder_service, links_service
    ):
        """
        A RangeSelector that starts and ends in the same element should be
        rewritten to an XPathSelector refinedBy a TextPositionSelector, for
        the sake of simplicity.
        """
        annotation = mock.Mock(target_uri="http://example.com")
        annotation.target_selectors = [
            {
                "type": "RangeSelector",
                "startContainer": "/div[1]/main[1]/article[1]/div[2]/p[339]",
                "startOffset": 12,
                "endContainer": "/div[1]/main[1]/article[1]/div[2]/p[339]",
                "endOffset": 43,
            }
        ]
        resource = AnnotationContext(annotation, groupfinder_service, links_service)

        selectors = AnnotationJSONLDPresenter(resource).target[0]["selector"]

        assert selectors == [
            {
                "type": "XPathSelector",
                "value": "/div[1]/main[1]/article[1]/div[2]/p[339]",
                "refinedBy": {"type": "TextPositionSelector", "start": 12, "end": 43},
            }
        ]

    def test_rewrites_rangeselectors_different_element(
        self, groupfinder_service, links_service
    ):
        """
        A RangeSelector that starts and ends in the different elements should
        be rewritten to a RangeSelector bounded by two XPathSelectors, each of
        which is refinedBy a "point"-like TextPositionSelector.
        """
        annotation = mock.Mock(target_uri="http://example.com")
        annotation.target_selectors = [
            {
                "type": "RangeSelector",
                "startContainer": "/div[1]/main[1]/article[1]/div[2]/h1[1]",
                "startOffset": 4,
                "endContainer": "/div[1]/main[1]/article[1]/div[2]/p[339]",
                "endOffset": 72,
            }
        ]
        resource = AnnotationContext(annotation, groupfinder_service, links_service)

        selectors = AnnotationJSONLDPresenter(resource).target[0]["selector"]

        assert selectors == [
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

    def test_ignores_malformed_rangeselectors(self, groupfinder_service, links_service):
        annotation = mock.Mock(target_uri="http://example.com")
        annotation.target_selectors = [
            {
                "type": "RangeSelector",
                "startContainer": "/div[1]/main[1]/article[1]/div[2]/h1[1]",
                "startOffset": 4,
                "endContainer": "/div[1]/main[1]/article[1]/div[2]/p[339]",
            }
        ]
        resource = AnnotationContext(annotation, groupfinder_service, links_service)

        target = AnnotationJSONLDPresenter(resource).target[0]

        assert "selector" not in target
