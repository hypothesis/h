from datetime import datetime, timedelta
from unittest import mock

import pytest

from h.models import Document, GroupMembership
from h.models.group import LMSRole
from h.schemas import ValidationError
from h.services.checkpoint import CheckpointService, factory
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


class TestHidesAnnotation:
    def test_it_is_false_for_a_none_user(self, svc, group, document, factories):
        annotation = self.annotation(factories, group, document)

        assert svc.hides_annotation(None, annotation) is False

    @pytest.mark.usefixtures("student_membership", "active_checkpoint")
    def test_it_hides_a_peers_annotation(self, svc, user, peer_annotation):
        assert svc.hides_annotation(user, peer_annotation) is True

    @pytest.mark.usefixtures("student_membership", "active_checkpoint")
    def test_it_shows_the_users_own_annotation(
        self, svc, user, group, document, factories
    ):
        own = self.annotation(factories, group, document, userid=user.userid)

        assert svc.hides_annotation(user, own) is False

    @pytest.mark.usefixtures("student_membership", "active_checkpoint")
    def test_it_shows_instructor_notes(
        self, svc, user, group, document, instructor, factories
    ):
        note = self.annotation(factories, group, document, userid=instructor.userid)

        assert svc.hides_annotation(user, note) is False

    @pytest.mark.usefixtures("student_membership", "active_checkpoint")
    def test_it_shows_instructor_replies_to_the_user(
        self, svc, user, group, document, instructor, factories
    ):
        own = self.annotation(factories, group, document, userid=user.userid)
        reply = self.annotation(
            factories, group, document, userid=instructor.userid, references=[own.id]
        )

        assert svc.hides_annotation(user, reply) is False

    @pytest.mark.usefixtures("student_membership", "active_checkpoint")
    def test_it_hides_instructor_replies_to_other_students(
        self, svc, user, group, document, instructor, factories
    ):
        other = self.annotation(
            factories, group, document, userid="acct:other@localhost"
        )
        reply = self.annotation(
            factories, group, document, userid=instructor.userid, references=[other.id]
        )

        assert svc.hides_annotation(user, reply) is True

    @pytest.mark.usefixtures("student_membership", "active_checkpoint")
    def test_it_ignores_annotations_on_a_different_document(
        self, svc, user, group, factories
    ):
        other_doc = factories.Document()
        peer = self.annotation(
            factories, group, other_doc, userid="acct:peer@localhost"
        )

        assert svc.hides_annotation(user, peer) is False

    @pytest.mark.usefixtures("student_membership", "revealed_checkpoint")
    def test_it_is_false_when_the_checkpoint_is_revealed(
        self, svc, user, peer_annotation
    ):
        assert svc.hides_annotation(user, peer_annotation) is False

    def annotation(self, factories, group, document, **kwargs):
        annotation = factories.Annotation(groupid=group.pubid, **kwargs)
        # The Annotation factory reassigns `document` from target_uri via its
        # make_metadata hook, so pin the checkpoint's document explicitly after.
        annotation.document = document
        self.db.flush()
        return annotation

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
    def instructor(self, factories, group):
        instructor = factories.User()
        self.membership(group, instructor, LMSRole.LMS_INSTRUCTOR)
        return instructor

    @pytest.fixture
    def peer_annotation(self, factories, group, document):
        return self.annotation(factories, group, document, userid="acct:peer@localhost")


class TestUpsert:
    def test_it_creates_a_new_checkpoint(self, svc, factories):
        group = factories.Group()

        checkpoint = svc.upsert_checkpoint(
            authority=group.authority,
            group_authority_provided_id=group.authority_provided_id,
            document_uri="http://example.com/page",
            reveal_date="2026-07-01T10:00:00",
        )

        assert checkpoint.group_id == group.id
        assert checkpoint.previous_checkpoint_id is None
        assert checkpoint.reveal_date == datetime(2026, 7, 1, 10, 0, 0)  # noqa: DTZ001

    def test_it_creates_a_checkpoint_with_no_reveal_date(self, svc, factories):
        group = factories.Group()

        checkpoint = svc.upsert_checkpoint(
            authority=group.authority,
            group_authority_provided_id=group.authority_provided_id,
            document_uri="http://example.com/page",
        )

        assert checkpoint.reveal_date is None

    def test_it_stores_a_timezone_aware_reveal_date_as_naive_utc(self, svc, factories):
        group = factories.Group()

        checkpoint = svc.upsert_checkpoint(
            authority=group.authority,
            group_authority_provided_id=group.authority_provided_id,
            document_uri="http://example.com/page",
            reveal_date="2026-07-01T10:00:00+02:00",
        )

        # 10:00 at +02:00 is 08:00 UTC, stored without tzinfo.
        assert checkpoint.reveal_date == datetime(2026, 7, 1, 8, 0, 0)  # noqa: DTZ001

    def test_it_updates_an_existing_checkpoint(self, svc, factories, db_session):
        group = factories.Group()
        document = factories.Document()
        factories.DocumentURI(document=document, uri="http://example.com/page")
        existing = factories.Checkpoint(
            group=group, document=document, reveal_date=None
        )
        # The bulk endpoint loads the checkpoint fresh; expire the cached instance
        # so db.get() reloads the row the conflict-update actually wrote.
        db_session.expire(existing)

        checkpoint = svc.upsert_checkpoint(
            authority=group.authority,
            group_authority_provided_id=group.authority_provided_id,
            document_uri="http://example.com/page",
            reveal_date="2026-07-01T10:00:00",
        )

        assert checkpoint.id == existing.id
        assert checkpoint.reveal_date == datetime(2026, 7, 1, 10, 0, 0)  # noqa: DTZ001

    def test_it_raises_for_an_invalid_reveal_date(self, svc, factories):
        group = factories.Group()

        with pytest.raises(ValidationError):
            svc.upsert_checkpoint(
                authority=group.authority,
                group_authority_provided_id=group.authority_provided_id,
                document_uri="http://example.com/page",
                reveal_date="not-a-date",
            )

    def test_it_returns_None_when_the_group_is_not_found(self, svc):
        assert (
            svc.upsert_checkpoint(
                authority="example.com",
                group_authority_provided_id="missing",
                document_uri="http://example.com/page",
            )
            is None
        )

    def test_it_returns_None_when_the_document_cannot_be_resolved(
        self, svc, factories, mocker
    ):
        group = factories.Group()
        query = mocker.Mock()
        query.first.return_value = None
        mocker.patch.object(Document, "find_or_create_by_uris", return_value=query)

        assert (
            svc.upsert_checkpoint(
                authority=group.authority,
                group_authority_provided_id=group.authority_provided_id,
                document_uri="http://example.com/page",
            )
            is None
        )


class TestSetInstructorRole:
    def test_it_sets_the_instructor_role(self, svc, factories, db_session):
        user = factories.User()
        group = factories.Group()
        membership = GroupMembership(user=user, group=group)
        db_session.add(membership)
        db_session.flush()

        svc.set_instructor_role(
            authority=user.authority,
            username=user.username,
            group_authority_provided_ids=[group.authority_provided_id],
        )

        assert membership.lms_role == LMSRole.LMS_INSTRUCTOR.value

    def test_it_only_sets_the_role_in_the_given_groups(
        self, svc, factories, db_session
    ):
        user = factories.User()
        group = factories.Group()
        other_group = factories.Group()
        membership = GroupMembership(user=user, group=group)
        other_membership = GroupMembership(user=user, group=other_group)
        db_session.add_all([membership, other_membership])
        db_session.flush()

        svc.set_instructor_role(
            authority=user.authority,
            username=user.username,
            group_authority_provided_ids=[group.authority_provided_id],
        )

        assert membership.lms_role == LMSRole.LMS_INSTRUCTOR.value
        assert other_membership.lms_role is None

    def test_it_does_nothing_when_the_user_is_not_found(self, svc):
        # A missing user is a no-op and must not raise.
        svc.set_instructor_role(
            authority="example.com",
            username="nonexistent",
            group_authority_provided_ids=["whatever"],
        )


class TestFactory:
    def test_it(self, pyramid_request):
        svc = factory(mock.sentinel.context, pyramid_request)

        assert isinstance(svc, CheckpointService)
        assert svc.db == pyramid_request.db


@pytest.fixture
def svc(db_session):
    return CheckpointService(db=db_session)
