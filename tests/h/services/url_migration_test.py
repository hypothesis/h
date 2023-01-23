from unittest.mock import Mock

import pytest
from h_matchers import Any

from h.services.url_migration import URLMigrationService


class TestURLMigrationService:
    def test_move_annotations_does_nothing_if_annotation_was_deleted(
        self, update_annotation, svc
    ):
        svc.move_annotations(
            ["id-that-does-not-exist"],
            "https://somesite.com",
            {"url": "https://example.org"},
        )
        update_annotation.assert_not_called()

    def test_move_annotations_does_nothing_if_url_no_longer_matches(
        self, db_session, factories, update_annotation, svc
    ):
        ann = factories.Annotation(target_uri="https://example.com")
        db_session.flush()

        svc.move_annotations(
            [ann.id],
            # Use a different URL to simulate the case where the annotation's
            # URL is changed in between a move being scheduled, and the move
            # being executed.
            "https://wrongsite.com",
            {"url": "https://example.org"},
        )

        assert ann.target_uri == "https://example.com"
        update_annotation.assert_not_called()

    def test_move_annotations_updates_urls(
        self, db_session, factories, pyramid_request, update_annotation, svc
    ):
        anns = [
            factories.Annotation(target_uri="https://example.com"),
            factories.Annotation(target_uri="https://example.com"),
        ]
        db_session.flush()

        svc.move_annotations(
            [anns[0].id, anns[1].id],
            "https://example.com",
            {"url": "https://example.org"},
        )

        assert update_annotation.call_count == 2
        for ann in anns[0:2]:
            update_annotation.assert_any_call(
                pyramid_request,
                ann.id,
                {"target_uri": "https://example.org"},
                update_timestamp=False,
                reindex_tag="URLMigrationService.move_annotations",
            )

    def test_move_annotations_updates_selectors(
        self, db_session, factories, pyramid_request, update_annotation, svc
    ):
        ann = factories.Annotation(target_uri="https://example.com")
        ann.target_selectors = [
            {"type": "TextQuoteSelector", "exact": "foobar"},
            {"type": "EPUBContentSelector", "cfi": "/2/4"},
        ]
        db_session.flush()

        svc.move_annotations(
            [ann.id],
            "https://example.com",
            {
                "url": "https://example.org",
                "selectors": [
                    # New selector that is not in existing selectors. This should be added.
                    {"type": "PageSelector", "label": "3"},
                    # Selector that matches an existing selector. This should not be duplicated.
                    {"type": "EPUBContentSelector", "cfi": "/2/4"},
                ],
            },
        )

        update_annotation.assert_called_once_with(
            pyramid_request,
            ann.id,
            {
                "target_uri": "https://example.org",
                "target_selectors": [
                    {"type": "TextQuoteSelector", "exact": "foobar"},
                    {"type": "EPUBContentSelector", "cfi": "/2/4"},
                    {"type": "PageSelector", "label": "3"},
                ],
            },
            update_timestamp=False,
            reindex_tag="URLMigrationService.move_annotations",
        )

    def test_move_annotations_updates_documents(
        self,
        db_session,
        factories,
        pyramid_request,
        update_annotation,
        transform_document,
        svc,
    ):
        ann = factories.Annotation(target_uri="https://example.com")
        db_session.flush()

        svc.move_annotations(
            [ann.id],
            "https://example.com",
            {
                "url": "https://example.org",
                "document": {"title": "The new example.com"},
            },
        )

        transform_document.assert_called_with(
            {"title": "The new example.com"}, "https://example.org"
        )
        update_annotation.assert_called_once_with(
            pyramid_request,
            ann.id,
            {
                "target_uri": "https://example.org",
                "document": transform_document.return_value,
            },
            update_timestamp=False,
            reindex_tag="URLMigrationService.move_annotations",
        )

    def test_move_annotations_by_url_moves_matching_annotations(
        self,
        db_session,
        factories,
        pyramid_request,
        update_annotation,
        move_annotations_task,
        svc,
    ):
        anns = [
            factories.Annotation(target_uri="https://example.com"),
            factories.Annotation(target_uri="https://example.com"),
            factories.Annotation(target_uri="https://othersite.com"),
            factories.Annotation(target_uri="https://example.com"),
        ]
        db_session.flush()

        svc.move_annotations_by_url(
            "https://example.com",
            {"url": "https://example.org"},
        )

        # First annotation should be moved synchronously.
        assert update_annotation.call_count == 1
        update_annotation.assert_called_with(
            pyramid_request,
            Any.of([a.id for a in anns]),
            {"target_uri": "https://example.org"},
            update_timestamp=False,
            reindex_tag="URLMigrationService.move_annotations",
        )
        pyramid_request.tm.commit.assert_called_once()

        moved_ann_id = update_annotation.call_args[0][1]
        remaining_ann_ids = [
            a.id
            for a in anns
            if a.target_uri == "https://example.com" and a.id != moved_ann_id
        ]

        # Remaining matching annotations should be moved in separate tasks.
        assert move_annotations_task.delay.call_count == 1
        move_annotations_task.delay.assert_called_once_with(
            Any.list.containing(remaining_ann_ids).only(),
            "https://example.com",
            {"url": "https://example.org"},
        )

    def test_move_annotations_by_url_handles_no_matches(
        self, db_session, factories, update_annotation, move_annotations_task, svc
    ):
        # Make sure there are some non-matching annotations in the DB.
        factories.Annotation(target_uri="https://foo.com")
        factories.Annotation(target_uri="https://bar.com")
        factories.Annotation(target_uri="https://baz.com")
        db_session.flush()

        svc.move_annotations_by_url(
            "https://example.com",
            {"url": "https://example.org"},
        )

        update_annotation.assert_not_called()
        move_annotations_task.delay.assert_not_called()

    @pytest.fixture(autouse=True)
    def transform_document(self, patch):
        return patch("h.services.url_migration.transform_document")

    @pytest.fixture(autouse=True)
    def update_annotation(self, patch):
        return patch("h.storage.update_annotation")

    @pytest.fixture(autouse=True)
    def move_annotations_task(self, patch):
        return patch("h.services.url_migration.move_annotations")

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.tm = Mock(spec_set=["commit"])
        return pyramid_request

    @pytest.fixture
    def svc(self, pyramid_request):
        return URLMigrationService(pyramid_request)
