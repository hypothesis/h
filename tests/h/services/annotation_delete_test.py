from datetime import datetime, timedelta
from unittest import mock

import pytest

from h.events import AnnotationEvent
from h.models import Annotation, AnnotationSlim
from h.services.annotation_delete import annotation_delete_service_factory


class TestAnnotationDeleteService:
    def test_it_marks_the_annotation_as_deleted(self, svc, annotation):
        ann = annotation()
        svc.delete(ann)

        assert ann.deleted

    def test_it_updates_the_updated_field(self, svc, annotation, datetime):
        ann = annotation()
        svc.delete(ann)

        assert ann.updated == datetime.utcnow.return_value

    def test_it_publishes_a_delete_event(self, svc, pyramid_request, annotation):
        ann = annotation()
        svc.delete(ann)

        expected_event = AnnotationEvent(pyramid_request, ann.id, "delete")
        actual_event = pyramid_request.notify_after_commit.call_args[0][0]
        assert (
            expected_event.request,
            expected_event.annotation_id,
            expected_event.action,
        ) == (actual_event.request, actual_event.annotation_id, actual_event.action)

    def test_it_deletes_all_annotations(self, svc, annotation):
        svc.delete = mock.create_autospec(svc.delete, spec_set=True)

        anns = [annotation(), annotation()]
        svc.delete_annotations(anns)

        assert svc.delete.mock_calls == [mock.call(anns[0]), mock.call(anns[1])]

    @pytest.mark.parametrize(
        "deleted,mins_ago,purged",
        [
            # Deleted more than 10 minutes ago... should be purged.
            (True, 30, True),
            (True, 3600, True),
            # Deleted less than 10 minutes ago... should NOT be purged.
            (True, -30, False),  # annotation from the future! wooOOOooo!
            (True, 0, False),
            (True, 1, False),
            (True, 9, False),
            # Not deleted... should NOT be purged.
            (False, -30, False),
            (False, 0, False),
            (False, 1, False),
            (False, 9, False),
            (False, 30, False),
            (False, 3600, False),
        ],
    )
    def test_bulk_delete(self, db_session, svc, factories, deleted, mins_ago, purged):
        updated = datetime.utcnow() - timedelta(minutes=mins_ago)
        annotation = factories.Annotation(deleted=deleted, updated=updated)
        annotation_slim = factories.AnnotationSlim(
            deleted=deleted, updated=updated, annotation=annotation
        )
        db_session.add(annotation)
        db_session.add(annotation_slim)

        svc.bulk_delete()

        if purged:
            assert not db_session.query(Annotation).count()
            assert not db_session.query(AnnotationSlim).count()
        else:
            assert db_session.query(Annotation).count() == 1
            assert db_session.query(AnnotationSlim).count() == 1

    @pytest.fixture
    def datetime(self, patch):
        return patch("h.services.annotation_delete.datetime")


@pytest.fixture
def annotation(factories):
    return lambda factories=factories: factories.Annotation()


# pylint:disable=unused-argument
@pytest.fixture
def svc(db_session, pyramid_request, annotation_write_service):
    pyramid_request.db = db_session
    return annotation_delete_service_factory({}, pyramid_request)


@pytest.fixture
def pyramid_request(pyramid_request):
    pyramid_request.notify_after_commit = mock.Mock()
    return pyramid_request
