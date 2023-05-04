from datetime import datetime as datetime_
from datetime import timedelta
from unittest.mock import sentinel

import pytest
from h_matchers import Any

from h import storage
from h.models.document import Document, DocumentURI
from h.schemas import ValidationError

pytestmark = pytest.mark.usefixtures("search_index")


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

    def test_update_timestamps_disabled(
        self, pyramid_request, annotation, annotation_data, datetime
    ):
        orig_updated = annotation.updated

        result = storage.update_annotation(
            pyramid_request, annotation.id, annotation_data, update_timestamp=False
        )

        assert orig_updated != datetime.utcnow.return_value
        assert result.updated == orig_updated

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

    def test_it_updates_document_if_uri_changed(
        self, pyramid_request, annotation, update_document_metadata
    ):
        result = storage.update_annotation(
            pyramid_request, annotation.id, {"target_uri": "https://new-url.com"}
        )

        update_document_metadata.assert_called_once_with(
            pyramid_request.db, annotation.target_uri, {}, {}, updated=Any()
        )
        assert result.document == update_document_metadata.return_value

    def test_it_does_not_update_document_if_no_document_or_uri_change(
        self, pyramid_request, annotation, update_document_metadata
    ):
        storage.update_annotation(pyramid_request, annotation.id, {})

        update_document_metadata.assert_not_called()

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
            annotation.id, tag="storage.update_annotation", schedule_in=60, force=False
        )

    def test_it_uses_custom_reindex_tag(
        self, annotation, pyramid_request, search_index
    ):
        storage.update_annotation(
            pyramid_request, annotation.id, {}, reindex_tag="h.services.SomeService"
        )

        search_index._queue.add_by_id.assert_called_once_with(  # pylint:disable=protected-access
            annotation.id, tag="h.services.SomeService", schedule_in=60, force=False
        )

    def test_it_forces_reindexing_if_update_timestamp_is_false(
        self, annotation, pyramid_request, search_index
    ):
        storage.update_annotation(
            pyramid_request, annotation.id, {}, update_timestamp=False
        )

        search_index._queue.add_by_id.assert_called_once_with(  # pylint:disable=protected-access
            annotation.id, tag=Any(), schedule_in=60, force=True
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
