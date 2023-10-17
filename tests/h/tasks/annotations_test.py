import pytest

from h.models import Annotation, AnnotationSlim
from h.tasks.annotations import fill_annotation_slim


class TestFillPKAndUserId:
    AUTHORITY_1 = "AUTHORITY_1"
    AUTHORITY_2 = "AUTHORITY_2"

    USERNAME_1 = "USERNAME_1"
    USERNAME_2 = "USERNAME_2"

    def test_it(self, factories, db_session):
        author = factories.User(authority=self.AUTHORITY_1, username=self.USERNAME_1)

        annos = factories.Annotation.create_batch(
            10,
            userid=author.userid,
        )
        factories.Annotation.create_batch(5)

        fill_annotation_slim(batch_size=10)

        assert db_session.query(AnnotationSlim).count() == 10
        assert (
            db_session.query(Annotation)
            .outerjoin(AnnotationSlim)
            .filter(AnnotationSlim.id.is_(None))
            .count()
            == 5
        )

        # Refresh data for the annotations
        _ = [db_session.refresh(anno) for anno in annos]

        for anno in annos:
            assert anno.slim.pubid == anno.id
            assert anno.slim.created == anno.created
            assert anno.slim.updated == anno.updated
            assert anno.slim.deleted == anno.deleted
            assert anno.slim.shared == anno.shared
            assert anno.slim.document_id == anno.document_id
            assert anno.slim.group_id == anno.group.id
            assert anno.slim.user_id == author.id

    @pytest.fixture(autouse=True)
    def celery(self, patch, db_session):
        cel = patch("h.tasks.annotations.celery", autospec=False)
        cel.request.db = db_session
        return cel
