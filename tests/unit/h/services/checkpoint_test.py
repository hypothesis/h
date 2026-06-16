from datetime import datetime, timedelta
from unittest import mock

import pytest

from h.models import Checkpoint, GroupMembership
from h.models.group import LMSRole
from h.services.checkpoint import CheckpointService, GroupNotFoundError, factory
from h.util.uri import normalize as uri_normalize


class TestActiveCheckpoint:
    def test_it_returns_an_unrevealed_checkpoint(self, svc, group, document):
        checkpoint = self.checkpoint(group, document, reveal_date=None)

        assert svc.active_checkpoint(group.id, "http://example.com/page") == checkpoint

    def test_it_returns_a_checkpoint_with_a_future_reveal_date(
        self, svc, group, document
    ):
        checkpoint = self.checkpoint(
            group,
            document,
            reveal_date=datetime.utcnow() + timedelta(days=1),  # noqa: DTZ003
        )

        assert svc.active_checkpoint(group.id, "http://example.com/page") == checkpoint

    def test_it_returns_None_when_the_checkpoint_is_revealed(
        self, svc, group, document
    ):
        self.checkpoint(
            group,
            document,
            reveal_date=datetime.utcnow() - timedelta(days=1),  # noqa: DTZ003
        )

        assert svc.active_checkpoint(group.id, "http://example.com/page") is None

    @pytest.mark.usefixtures("document")
    def test_it_returns_None_when_there_is_no_checkpoint(self, svc, group):
        assert svc.active_checkpoint(group.id, "http://example.com/page") is None

    def test_it_returns_None_for_a_different_group(
        self, svc, group, document, factories
    ):
        self.checkpoint(group, document, reveal_date=None)
        other_group = factories.Group()

        assert svc.active_checkpoint(other_group.id, "http://example.com/page") is None

    def test_it_resolves_the_uri_to_the_document(self, svc, group, document, factories):
        # A second URI on the same document (e.g. a PDF fingerprint) must
        # resolve to the same checkpoint.
        factories.DocumentURI(document=document, uri="urn:x-pdf:the-fingerprint")
        checkpoint = self.checkpoint(group, document, reveal_date=None)

        assert (
            svc.active_checkpoint(group.id, "urn:x-pdf:the-fingerprint") == checkpoint
        )

    def test_it_returns_None_for_an_unknown_uri(self, svc, group, document):
        self.checkpoint(group, document, reveal_date=None)

        assert svc.active_checkpoint(group.id, "http://example.com/other") is None

    def checkpoint(self, group, document, reveal_date):
        return self.factories.Checkpoint(
            group=group, document=document, reveal_date=reveal_date
        )

    @pytest.fixture(autouse=True)
    def _factories(self, factories):
        self.factories = factories

    @pytest.fixture
    def group(self, factories):
        return factories.Group()

    @pytest.fixture
    def document(self, factories):
        document = factories.Document()
        factories.DocumentURI(document=document, uri="http://example.com/page")
        return document


class TestHiddenScopes:
    def test_it_returns_empty_for_a_none_user(self, svc):
        assert svc.hidden_scopes(None) == []

    def test_it_returns_empty_when_the_user_has_no_checkpoints(self, svc, user):
        assert svc.hidden_scopes(user) == []

    @pytest.mark.usefixtures("active_checkpoint")
    def test_it_returns_empty_when_the_user_is_not_a_member(self, svc, user):
        assert svc.hidden_scopes(user) == []

    @pytest.mark.usefixtures("active_checkpoint", "instructor_membership")
    def test_it_returns_empty_for_an_instructor(self, svc, user):
        assert svc.hidden_scopes(user) == []

    @pytest.mark.usefixtures("revealed_checkpoint", "student_membership")
    def test_it_returns_empty_when_the_checkpoint_is_revealed(self, svc, user):
        assert svc.hidden_scopes(user) == []

    @pytest.mark.usefixtures("active_checkpoint", "student_membership")
    def test_it_returns_a_scope_for_a_student(self, svc, user, group):
        [scope] = svc.hidden_scopes(user)

        assert scope.group_pubid == group.pubid
        # The scope carries the normalized URIs, matching ES `target.scope`.
        assert scope.uris == [uri_normalize("http://example.com/page")]

    @pytest.mark.usefixtures("active_checkpoint", "null_role_membership")
    def test_it_restricts_members_with_no_lms_role(self, svc, user):
        # Default-deny: anyone not explicitly an instructor is restricted.
        assert len(svc.hidden_scopes(user)) == 1

    @pytest.mark.usefixtures("active_checkpoint", "student_membership")
    def test_it_collects_instructor_userids(self, svc, user, group, factories):
        instructor = factories.User()
        self.membership(group, instructor, LMSRole.LMS_INSTRUCTOR)

        [scope] = svc.hidden_scopes(user)

        assert scope.instructor_userids == [instructor.userid]

    @pytest.mark.usefixtures("active_checkpoint", "student_membership")
    def test_it_collects_the_users_own_annotation_ids(
        self, svc, user, group, factories
    ):
        own = factories.Annotation(userid=user.userid, groupid=group.pubid)
        # An annotation by someone else in the group is not "own".
        factories.Annotation(groupid=group.pubid)

        [scope] = svc.hidden_scopes(user)

        assert scope.own_annotation_ids == [own.id]

    def membership(self, group, user, lms_role):
        membership = GroupMembership(
            user=user, group=group, lms_role=lms_role.value if lms_role else None
        )
        self.db.add(membership)
        self.db.flush()
        return membership

    @pytest.fixture(autouse=True)
    def _db(self, db_session):
        self.db = db_session

    @pytest.fixture
    def user(self, factories):
        return factories.User()

    @pytest.fixture
    def group(self, factories):
        return factories.Group()

    @pytest.fixture
    def document(self, factories):
        document = factories.Document()
        factories.DocumentURI(document=document, uri="http://example.com/page")
        return document

    @pytest.fixture
    def active_checkpoint(self, factories, group, document):
        return factories.Checkpoint(group=group, document=document, reveal_date=None)

    @pytest.fixture
    def revealed_checkpoint(self, factories, group, document):
        return factories.Checkpoint(
            group=group,
            document=document,
            reveal_date=datetime.utcnow() - timedelta(days=1),  # noqa: DTZ003
        )

    @pytest.fixture
    def student_membership(self, group, user):
        return self.membership(group, user, LMSRole.LMS_STUDENT)

    @pytest.fixture
    def instructor_membership(self, group, user):
        return self.membership(group, user, LMSRole.LMS_INSTRUCTOR)

    @pytest.fixture
    def null_role_membership(self, group, user):
        return self.membership(group, user, None)


class TestUpsert:
    def test_it_creates_a_checkpoint(self, svc, group):
        checkpoint = svc.upsert(
            authority=group.authority,
            authority_provided_id=group.authority_provided_id,
            document_url="http://example.com/page",
            reveal_date=None,
        )

        assert checkpoint.group_id == group.id
        assert checkpoint.reveal_date is None
        assert checkpoint.previous_checkpoint_id is None

    def test_it_creates_the_document_when_it_does_not_exist(self, svc, group):
        checkpoint = svc.upsert(
            authority=group.authority,
            authority_provided_id=group.authority_provided_id,
            document_url="http://example.com/brand-new",
            reveal_date=None,
        )

        normalized = [uri.uri_normalized for uri in checkpoint.document.document_uris]
        assert uri_normalize("http://example.com/brand-new") in normalized

    def test_it_reuses_an_existing_document(self, svc, group, factories):
        document = factories.Document()
        factories.DocumentURI(document=document, uri="http://example.com/page")

        checkpoint = svc.upsert(
            authority=group.authority,
            authority_provided_id=group.authority_provided_id,
            document_url="http://example.com/page",
            reveal_date=None,
        )

        assert checkpoint.document_id == document.id

    def test_it_overrides_the_reveal_date_of_an_existing_checkpoint(
        self, svc, group, db_session
    ):
        first = svc.upsert(
            authority=group.authority,
            authority_provided_id=group.authority_provided_id,
            document_url="http://example.com/page",
            reveal_date=datetime(2026, 7, 1),  # noqa: DTZ001
        )
        second = svc.upsert(
            authority=group.authority,
            authority_provided_id=group.authority_provided_id,
            document_url="http://example.com/page",
            reveal_date=datetime(2026, 6, 15),  # noqa: DTZ001
        )

        # Same checkpoint, newest write wins, no duplicate row.
        assert second.id == first.id
        assert second.reveal_date == datetime(2026, 6, 15)  # noqa: DTZ001
        assert db_session.query(Checkpoint).count() == 1

    def test_it_merges_documents_that_share_the_url(self, svc, group, factories):
        # Two documents claiming the same URL must collapse into one.
        for _ in range(2):
            document = factories.Document()
            factories.DocumentURI(document=document, uri="http://example.com/dup")

        checkpoint = svc.upsert(
            authority=group.authority,
            authority_provided_id=group.authority_provided_id,
            document_url="http://example.com/dup",
            reveal_date=None,
        )

        normalized = [uri.uri_normalized for uri in checkpoint.document.document_uris]
        assert uri_normalize("http://example.com/dup") in normalized

    def test_it_raises_when_the_group_is_not_found(self, svc, group):
        with pytest.raises(GroupNotFoundError):
            svc.upsert(
                authority=group.authority,
                authority_provided_id="does-not-exist",
                document_url="http://example.com/page",
                reveal_date=None,
            )

    @pytest.fixture
    def group(self, factories):
        return factories.Group(authority_provided_id="test-authority-provided-id")


class TestFactory:
    def test_it(self, pyramid_request):
        svc = factory(mock.sentinel.context, pyramid_request)

        assert isinstance(svc, CheckpointService)
        assert svc.db == pyramid_request.db


@pytest.fixture
def svc(db_session):
    return CheckpointService(db=db_session)
