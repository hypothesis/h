import pytest

from h.models import Annotation
from h.tasks.annotations import fill_pk_and_user_id


class TestFillPKAndUserId:
    AUTHORITY_1 = "AUTHORITY_1"
    AUTHORITY_2 = "AUTHORITY_2"

    USERNAME_1 = "USERNAME_1"
    USERNAME_2 = "USERNAME_2"

    def test_it(self, factories, db_session):
        author_1 = factories.User(authority=self.AUTHORITY_1, username=self.USERNAME_1)
        author_2 = factories.User(authority=self.AUTHORITY_2, username=self.USERNAME_2)

        annos_1 = factories.Annotation.create_batch(
            5,
            userid=author_1.userid,
        )
        annos_2 = factories.Annotation.create_batch(
            5,
            userid=author_2.userid,
        )
        factories.Annotation.create_batch(
            5,
            userid=author_2.userid,
        )

        fill_pk_and_user_id(batch_size=10)

        # Only one batch of 10 was processed, those have PKs now
        assert (
            db_session.query(Annotation).filter(Annotation.pk.is_not(None)).count()
            == 10
        )
        assert db_session.query(Annotation).filter(Annotation.pk.is_(None)).count() == 5

        # Refresh data for the annotations
        _ = [db_session.refresh(anno) for anno in annos_1 + annos_2]
        # user_id was updated with the right value
        assert {anno.user_id for anno in annos_1} == {author_1.id}
        assert {anno.user_id for anno in annos_2} == {author_2.id}

    @pytest.fixture(autouse=True)
    def celery(self, patch, db_session):
        cel = patch("h.tasks.annotations.celery", autospec=False)
        cel.request.db = db_session
        return cel
