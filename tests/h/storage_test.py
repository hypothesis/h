from datetime import datetime as datetime_
from datetime import timedelta
from unittest.mock import create_autospec, sentinel

import pytest
import sqlalchemy as sa
from h_matchers import Any

from h import storage
from h.models.annotation import Annotation
from h.models.document import Document, DocumentURI
from h.schemas import ValidationError
from h.security import Permission
from h.traversal.group import GroupContext

pytestmark = pytest.mark.usefixtures("search_index")


class TestFetchAnnotation:
    def test_it_fetches_and_returns_the_annotation(self, db_session, factories):
        annotation = factories.Annotation()

        actual = storage.fetch_annotation(db_session, annotation.id)
        assert annotation == actual

    def test_it_does_not_crash_if_id_is_invalid(self, db_session):
        assert storage.fetch_annotation(db_session, "foo") is None


class TestFetchOrderedAnnotations:
    def test_it_returns_annotations_for_ids_in_the_same_order(
        self, db_session, factories
    ):
        ann_1 = factories.Annotation(userid="luke")
        ann_2 = factories.Annotation(userid="luke")

        assert [ann_2, ann_1] == storage.fetch_ordered_annotations(
            db_session, [ann_2.id, ann_1.id]
        )
        assert [ann_1, ann_2] == storage.fetch_ordered_annotations(
            db_session, [ann_1.id, ann_2.id]
        )

    def test_it_allows_to_change_the_query(self, db_session, factories):
        ann_1 = factories.Annotation(userid="luke")
        ann_2 = factories.Annotation(userid="maria")

        def only_maria(query):
            return query.filter(Annotation.userid == "maria")

        assert [ann_2] == storage.fetch_ordered_annotations(
            db_session, [ann_2.id, ann_1.id], query_processor=only_maria
        )

    def test_it_handles_empty_ids(self):
        results = storage.fetch_ordered_annotations(sentinel.db_session, ids=[])

        assert results == []


class TestExpandURI:
    @pytest.mark.parametrize(
        "normalized,expected_uris",
        (
            (False, ["http://example.com/"]),
            (True, ["httpx://example.com"]),
        ),
    )
    def test_expand_uri_no_document(self, db_session, normalized, expected_uris):
        uris = storage.expand_uri(
            db_session, "http://example.com/", normalized=normalized
        )

        assert uris == expected_uris

    @pytest.mark.parametrize(
        "normalized,expected_uris",
        (
            (False, ["http://example.com/"]),
            (True, ["httpx://example.com"]),
        ),
    )
    def test_expand_uri_document_doesnt_expand_canonical_uris(
        self, db_session, normalized, expected_uris
    ):
        document = Document(
            document_uris=[
                DocumentURI(
                    uri="http://example.com/",
                    type="rel-canonical",
                    claimant="http://example.com",
                ),
                DocumentURI(
                    uri="http://noise.example.com/", claimant="http://example.com"
                ),
            ]
        )
        db_session.add(document)
        db_session.flush()

        uris = storage.expand_uri(
            db_session, "http://example.com/", normalized=normalized
        )

        assert uris == expected_uris

    @pytest.mark.parametrize(
        "normalized,expected_uris",
        (
            (False, ["http://example.com/", "http://alt.example.com/"]),
            (True, ["httpx://example.com", "httpx://alt.example.com"]),
        ),
    )
    def test_expand_uri_document_uris(self, db_session, normalized, expected_uris):
        document = Document(
            document_uris=[
                DocumentURI(uri="http://example.com/", claimant="http://example.com"),
                DocumentURI(
                    uri="http://alt.example.com/", claimant="http://example.com"
                ),
            ]
        )
        db_session.add(document)
        db_session.flush()

        uris = storage.expand_uri(
            db_session, "http://alt.example.com/", normalized=normalized
        )

        assert uris == expected_uris


class TestCreateAnnotation:
    def test_it(self, pyramid_request, annotation_data, datetime):
        annotation = storage.create_annotation(pyramid_request, annotation_data)

        for param, value in annotation_data.items():
            assert getattr(annotation, param) == value

        assert annotation.created == datetime.utcnow.return_value
        assert annotation.updated == datetime.utcnow.return_value

        assert sa.inspect(annotation).persistent  # We saved it to the DB

    def test_it_validates_the_group_scope(
        self, pyramid_request, annotation_data, group, _validate_group_scope
    ):
        storage.create_annotation(pyramid_request, annotation_data)

        _validate_group_scope.assert_called_once_with(
            group, annotation_data["target_uri"]
        )

    def test_it_adds_document_metadata(
        self, pyramid_request, annotation_data, update_document_metadata, datetime
    ):
        annotation_data["document"] = {
            "document_meta_dicts": sentinel.document_meta_dicts,
            "document_uri_dicts": sentinel.document_uri_dicts,
        }

        annotation = storage.create_annotation(pyramid_request, annotation_data)

        update_document_metadata.assert_called_once_with(
            pyramid_request.db,
            annotation_data["target_uri"],
            sentinel.document_meta_dicts,
            sentinel.document_uri_dicts,
            created=datetime.utcnow.return_value,
            updated=datetime.utcnow.return_value,
        )
        assert annotation.document == update_document_metadata.return_value

    def test_it_queues_the_search_index(
        self, pyramid_request, annotation_data, search_index
    ):
        annotation = storage.create_annotation(pyramid_request, annotation_data)

        search_index._queue.add_by_id.assert_called_once_with(  # pylint:disable=protected-access
            annotation.id, tag="storage.create_annotation", schedule_in=60
        )

    def test_it_sets_the_group_to_match_the_parent_for_replies(
        self, pyramid_request, annotation_data, factories, other_group
    ):
        parent_annotation = factories.Annotation(group=other_group)
        annotation_data["references"] = [parent_annotation.id]

        annotation = storage.create_annotation(pyramid_request, annotation_data)

        assert annotation.groupid
        assert annotation.group == parent_annotation.group

    def test_it_raises_if_parent_annotation_does_not_exist(
        self, pyramid_request, annotation_data
    ):
        annotation_data["references"] = ["MISSING_ID"]

        with pytest.raises(ValidationError):
            storage.create_annotation(pyramid_request, annotation_data)

    def test_it_raises_if_the_group_doesnt_exist(
        self, pyramid_request, annotation_data
    ):
        annotation_data["groupid"] = "MISSING_ID"

        with pytest.raises(ValidationError):
            storage.create_annotation(pyramid_request, annotation_data)

    def test_it_raises_if_write_permission_is_missing(
        self, pyramid_request, annotation_data, has_permission
    ):
        has_permission.return_value = False

        with pytest.raises(ValidationError):
            storage.create_annotation(pyramid_request, annotation_data)

        has_permission.assert_called_once_with(
            Permission.Group.WRITE, context=Any.instance_of(GroupContext)
        )

    def test_it_does_not_crash_if_target_selectors_is_empty(
        self, pyramid_request, annotation_data
    ):
        # Page notes have [] for target_selectors.
        annotation_data["target_selectors"] = []

        storage.create_annotation(pyramid_request, annotation_data)

    @pytest.mark.xfail(reason="This test passed before due to over fixturing")
    def test_it_does_not_crash_if_no_text_or_tags(
        self, pyramid_request, annotation_data
    ):
        # Highlights have no text or tags.
        annotation_data["text"] = annotation_data["tags"] = ""

        # ValueError: Attribute 'tags' does not accept objects of type <class 'str'>
        # So what should this be? None?
        storage.create_annotation(pyramid_request, annotation_data)

    @pytest.fixture
    def other_group(self, factories):
        # Set an authority_provided_id so our group_id is not None
        return factories.OpenGroup(authority_provided_id="other_group_auth_id")

    @pytest.fixture
    def has_permission(self, pyramid_request):
        pyramid_request.has_permission = create_autospec(pyramid_request.has_permission)
        return pyramid_request.has_permission


class TestUpdateAnnotation:
    def test_it(self, pyramid_request, annotation, annotation_data, datetime):
        result = storage.update_annotation(
            pyramid_request, annotation.id, annotation_data
        )

        assert result == annotation

        for param, value in annotation_data.items():
            assert getattr(result, param) == value

        assert result.created != datetime.utcnow.return_value
        assert result.updated == datetime.utcnow.return_value

    def test_it_validates_the_group_scope(
        self, pyramid_request, annotation, _validate_group_scope
    ):
        storage.update_annotation(
            pyramid_request, annotation.id, {"target_uri": "sentinel.target_uri"}
        )

        _validate_group_scope.assert_called_once_with(
            annotation.group, "sentinel.target_uri"
        )

    def test_it_doesnt_validates_the_group_scope_if_target_uri_missing(
        self, pyramid_request, annotation, _validate_group_scope
    ):
        storage.update_annotation(pyramid_request, annotation.id, {})

        _validate_group_scope.assert_not_called()

    def test_it_updates_extras(self, pyramid_request, annotation):
        annotation.extra = {"old_key": "old_value"}
        pyramid_request.db.flush()

        result = storage.update_annotation(
            pyramid_request, annotation.id, {"extra": {"new_key": "new_value"}}
        )

        assert result.extra == {"new_key": "new_value", "old_key": "old_value"}

    def test_it_updates_document_metadata(
        self, pyramid_request, annotation, update_document_metadata, datetime
    ):
        result = storage.update_annotation(
            pyramid_request,
            annotation.id,
            {
                "document": {
                    "document_meta_dicts": sentinel.document_meta_dicts,
                    "document_uri_dicts": sentinel.document_uri_dicts,
                }
            },
        )

        update_document_metadata.assert_called_once_with(
            pyramid_request.db,
            annotation.target_uri,
            sentinel.document_meta_dicts,
            sentinel.document_uri_dicts,
            updated=datetime.utcnow.return_value,
        )
        assert result.document == update_document_metadata.return_value

    def test_it_uses_the_updated_group_not_the_old_one(
        self, pyramid_request, annotation, group
    ):
        assert annotation.groupid != group.pubid
        assert annotation.group != group

        result = storage.update_annotation(
            pyramid_request, annotation.id, {"groupid": group.pubid}
        )

        assert result.groupid == group.pubid
        assert result.group == group

    def test_it_does_not_call_update_document_meta_if_no_document_in_data(
        self, pyramid_request, annotation, update_document_metadata
    ):
        storage.update_annotation(pyramid_request, annotation.id, {})

        update_document_metadata.assert_not_called()

    def test_it_raises_if_missing_group(self, pyramid_request, annotation):
        with pytest.raises(ValidationError):
            storage.update_annotation(
                pyramid_request, annotation.id, {"groupid": "MISSING_ID"}
            )

    def test_it_queues_the_annotation_for_syncing_to_Elasticsearch(
        self, annotation, pyramid_request, search_index
    ):
        storage.update_annotation(pyramid_request, annotation.id, {})

        search_index._queue.add_by_id.assert_called_once_with(  # pylint:disable=protected-access
            annotation.id, tag="storage.update_annotation", schedule_in=60
        )

    @pytest.fixture
    def annotation(self, factories):
        return factories.Annotation()


class TestValidateGroupScope:
    def test_it_allows_matching_scopes(self, scoped_group):
        storage._validate_group_scope(  # pylint:disable=protected-access
            scoped_group, "http://inscope.example.com"
        )

    def test_it_allows_mismatching_scopes_if_a_group_has_no_scopes(
        self, scoped_group, url_in_scope
    ):
        scoped_group.scopes = []

        storage._validate_group_scope(  # pylint:disable=protected-access
            scoped_group, "http://not-inscope.example.com"
        )

        url_in_scope.assert_not_called()

    def test_it_allows_mismatching_scopes_if_enforce_is_False(
        self, scoped_group, url_in_scope
    ):
        scoped_group.enforce_scope = False

        storage._validate_group_scope(  # pylint:disable=protected-access
            scoped_group, "http://not-inscope.example.com"
        )

        url_in_scope.assert_not_called()

    def test_it_catches_mismatching_scopes(self, scoped_group, url_in_scope):
        url_in_scope.return_value = False

        with pytest.raises(ValidationError):
            storage._validate_group_scope(  # pylint:disable=protected-access
                scoped_group, "http://not-inscope.example.com"
            )

    @pytest.fixture
    def scoped_group(self, factories):
        return factories.OpenGroup(
            enforce_scope=True,
            scopes=[factories.GroupScope(scope="http://inscope.example.com")],
        )

    @pytest.fixture
    def url_in_scope(self, patch):
        return patch("h.storage.url_in_scope")


@pytest.fixture
def group(factories):
    # Set an authority_provided_id so our group_id is not None
    return factories.OpenGroup(authority_provided_id="group_auth_id")


@pytest.fixture
def user(factories):
    return factories.User()


@pytest.fixture
def annotation_data(user, group):
    return {
        "userid": user.userid,
        "text": "text",
        "tags": ["one", "two"],
        "shared": False,
        "target_uri": "http://www.example.com/example.html",
        "groupid": group.pubid,
        "references": [],
        "target_selectors": ["selector_one", "selector_two"],
        "document": {"document_uri_dicts": [], "document_meta_dicts": []},
    }


@pytest.fixture
def datetime(patch):
    datetime = patch("h.storage.datetime")
    datetime.utcnow.return_value = datetime_.utcnow() + timedelta(hours=1)
    return datetime


@pytest.fixture
def _validate_group_scope(patch):
    return patch("h.storage._validate_group_scope")


@pytest.fixture
def update_document_metadata(patch, factories):
    update_document_metadata = patch("h.storage.update_document_metadata")
    update_document_metadata.return_value = factories.Document()
    return update_document_metadata
