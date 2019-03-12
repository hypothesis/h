# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import copy

import pytest
import mock

from h.models.annotation import Annotation
from h.models.document import Document, DocumentURI

from h import storage
from h.schemas import ValidationError


class FakeGroup(object):
    def __acl__(self):
        return []

    @property
    def scopes(self):
        return []


class TestFetchAnnotation(object):
    def test_it_fetches_and_returns_the_annotation(self, db_session, factories):
        annotation = factories.Annotation()

        actual = storage.fetch_annotation(db_session, annotation.id)
        assert annotation == actual

    def test_it_does_not_crash_if_id_is_invalid(self, db_session):
        assert storage.fetch_annotation(db_session, "foo") is None


class TestFetchOrderedAnnotations(object):
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


class TestExpandURI(object):
    def test_expand_uri_no_document(self, db_session):
        actual = storage.expand_uri(db_session, "http://example.com/")
        assert actual == ["http://example.com/"]

    def test_expand_uri_document_doesnt_expand_canonical_uris(self, db_session):
        document = Document(
            document_uris=[
                DocumentURI(uri="http://foo.com/", claimant="http://example.com"),
                DocumentURI(uri="http://bar.com/", claimant="http://example.com"),
                DocumentURI(
                    uri="http://example.com/",
                    type="rel-canonical",
                    claimant="http://example.com",
                ),
            ]
        )
        db_session.add(document)
        db_session.flush()

        assert storage.expand_uri(db_session, "http://example.com/") == [
            "http://example.com/"
        ]

    def test_expand_uri_document_uris(self, db_session):
        document = Document(
            document_uris=[
                DocumentURI(uri="http://foo.com/", claimant="http://bar.com"),
                DocumentURI(uri="http://bar.com/", claimant="http://bar.com"),
            ]
        )
        db_session.add(document)
        db_session.flush()

        assert storage.expand_uri(db_session, "http://foo.com/") == [
            "http://foo.com/",
            "http://bar.com/",
        ]


@pytest.mark.usefixtures("models", "group_service", "update_document_metadata")
class TestCreateAnnotation(object):
    def test_it_fetches_parent_annotation_for_replies(
        self, fetch_annotation, pyramid_config, pyramid_request, group_service
    ):

        # Make the annotation's parent belong to 'test-group'.
        fetch_annotation.return_value.groupid = "test-group"

        # The request will need permission to write to 'test-group'.
        pyramid_config.testing_securitypolicy(
            "acct:foo@example.com", groupids=["group:test-group"]
        )

        data = self.annotation_data()

        # The annotation is a reply.
        data["references"] = ["parent_annotation_id"]

        storage.create_annotation(pyramid_request, data, group_service)

        fetch_annotation.assert_called_once_with(
            pyramid_request.db, "parent_annotation_id"
        )

    def test_it_sets_group_for_replies(
        self, fetch_annotation, models, pyramid_config, pyramid_request, group_service
    ):
        # Make the annotation's parent belong to 'test-group'.
        fetch_annotation.return_value.groupid = "test-group"

        # The request will need permission to write to 'test-group'.
        pyramid_config.testing_securitypolicy(
            "acct:foo@example.com", groupids=["group:test-group"]
        )

        data = self.annotation_data()
        assert data["groupid"] != "test-group"

        # The annotation is a reply.
        data["references"] = ["parent_annotation_id"]

        storage.create_annotation(pyramid_request, data, group_service)

        assert models.Annotation.call_args[1]["groupid"] == "test-group"

    def test_it_raises_if_parent_annotation_does_not_exist(
        self, fetch_annotation, pyramid_request, group_service
    ):
        fetch_annotation.return_value = None

        data = self.annotation_data()

        # The annotation is a reply.
        data["references"] = ["parent_annotation_id"]

        with pytest.raises(ValidationError) as exc:
            storage.create_annotation(pyramid_request, data, group_service)

        assert str(exc.value).startswith("references.0: ")

    def test_it_finds_the_group(self, pyramid_request, pyramid_config, group_service):
        data = self.annotation_data()
        data["groupid"] = "foo-group"

        storage.create_annotation(pyramid_request, data, group_service)

        group_service.find.assert_called_once_with("foo-group")

    def test_it_allows_when_user_has_write_permission(
        self, pyramid_request, pyramid_config, models, group_service
    ):
        pyramid_config.testing_securitypolicy("userid", permissive=True)
        group_service.find.return_value = FakeGroup()

        data = self.annotation_data()
        data["groupid"] = "foo-group"

        # this should not raise
        result = storage.create_annotation(pyramid_request, data, group_service)

        assert result == models.Annotation.return_value

    def test_it_raises_when_user_is_missing_write_permission(
        self, pyramid_request, pyramid_config, group_service
    ):
        pyramid_config.testing_securitypolicy("userid", permissive=False)
        group_service.find.return_value = FakeGroup()

        data = self.annotation_data()
        data["groupid"] = "foo-group"

        with pytest.raises(ValidationError) as exc:
            storage.create_annotation(pyramid_request, data, group_service)

        assert str(exc.value).startswith("group: ")

    def test_it_allows_when_unscoped_group(
        self, pyramid_request, pyramid_config, group_service, factories, models
    ):
        group_service.find.return_value = factories.OpenGroup()

        data = self.annotation_data()
        data["target_uri"] = "http://www.foo.com/boo/bah.html"

        # this should not raise
        result = storage.create_annotation(pyramid_request, data, group_service)

        assert result == models.Annotation.return_value

    def test_it_allows_scope_mismatch_when_enforce_scope_is_False(
        self, pyramid_request, pyramid_config, group_service, scoped_open_group, models
    ):
        scoped_open_group.enforce_scope = False
        group_service.find.return_value = scoped_open_group
        data = self.annotation_data()
        # This target URI is not within any of the group's defined scopes
        data["target_uri"] = "http://www.foo.com/boo/bah.html"

        # This will not raise because ``enforce_scope`` is set to False for the
        # annotation's group
        result = storage.create_annotation(pyramid_request, data, group_service)

        assert result == models.Annotation.return_value

    def test_it_allows_when_target_uri_matches_single_group_scope(
        self, pyramid_request, pyramid_config, group_service, scoped_open_group, models
    ):
        group_service.find.return_value = scoped_open_group
        data = self.annotation_data()
        data["target_uri"] = "http://www.foo.com/boo/bah.html"

        # this should not raise
        result = storage.create_annotation(pyramid_request, data, group_service)

        assert result == models.Annotation.return_value

    def test_it_allows_when_target_uri_matches_multiple_group_scope(
        self, pyramid_request, pyramid_config, group_service, factories, models
    ):
        scope = factories.GroupScope(scope="http://www.foo.com")
        scope2 = factories.GroupScope(scope="http://www.bar.com")
        group_service.find.return_value = factories.OpenGroup(scopes=[scope, scope2])
        data = self.annotation_data()
        data["target_uri"] = "http://www.bar.com/boo/bah.html"

        # this should not raise
        result = storage.create_annotation(pyramid_request, data, group_service)

        assert result == models.Annotation.return_value

    def test_it_raises_when_group_scope_mismatch(
        self, pyramid_request, pyramid_config, group_service, scoped_open_group
    ):
        group_service.find.return_value = scoped_open_group
        data = self.annotation_data()
        data["target_uri"] = "http://www.bar.com/bing.html"

        with pytest.raises(ValidationError) as exc:
            storage.create_annotation(pyramid_request, data, group_service)

        assert str(exc.value).startswith("group scope: ")

    def test_it_raises_when_group_could_not_be_found(
        self, pyramid_request, pyramid_config, group_service
    ):
        pyramid_config.testing_securitypolicy("userid", permissive=True)
        group_service.find.return_value = None
        data = self.annotation_data()
        data["groupid"] = "missing-group"

        with pytest.raises(ValidationError) as exc:
            storage.create_annotation(pyramid_request, data, group_service)

        assert str(exc.value).startswith("group: ")

    def test_it_inits_an_Annotation_model(self, models, pyramid_request, group_service):
        data = self.annotation_data()

        storage.create_annotation(pyramid_request, copy.deepcopy(data), group_service)

        del data["document"]
        models.Annotation.assert_called_once_with(**data)

    def test_it_adds_the_annotation_to_the_database(
        self, models, pyramid_request, group_service, fake_db_session
    ):
        pyramid_request.db = fake_db_session
        storage.create_annotation(
            pyramid_request, self.annotation_data(), group_service
        )

        assert models.Annotation.return_value in pyramid_request.db.added

    def test_it_updates_the_document_metadata_from_the_annotation(
        self, models, pyramid_request, datetime, group_service, update_document_metadata
    ):
        annotation_data = self.annotation_data()
        annotation_data["document"][
            "document_meta_dicts"
        ] = mock.sentinel.document_meta_dicts
        annotation_data["document"][
            "document_uri_dicts"
        ] = mock.sentinel.document_uri_dicts

        storage.create_annotation(pyramid_request, annotation_data, group_service)

        update_document_metadata.assert_called_once_with(
            pyramid_request.db,
            models.Annotation.return_value.target_uri,
            mock.sentinel.document_meta_dicts,
            mock.sentinel.document_uri_dicts,
            created=datetime.utcnow(),
            updated=datetime.utcnow(),
        )

    def test_it_sets_the_annotations_document_id(
        self, models, pyramid_request, group_service, update_document_metadata
    ):
        annotation_data = self.annotation_data()

        document = mock.Mock()
        update_document_metadata.return_value = document

        ann = storage.create_annotation(pyramid_request, annotation_data, group_service)

        assert ann.document == document

    def test_it_returns_the_annotation(self, models, pyramid_request, group_service):
        annotation = storage.create_annotation(
            pyramid_request, self.annotation_data(), group_service
        )

        assert annotation == models.Annotation.return_value

    def test_it_does_not_crash_if_target_selectors_is_empty(
        self, pyramid_request, group_service
    ):
        # Page notes have [] for target_selectors.
        data = self.annotation_data()
        data["target_selectors"] = []

        storage.create_annotation(pyramid_request, data, group_service)

    def test_it_does_not_crash_if_no_text_or_tags(self, pyramid_request, group_service):
        # Highlights have no text or tags.
        data = self.annotation_data()
        data["text"] = data["tags"] = ""

        storage.create_annotation(pyramid_request, data, group_service)

    def annotation_data(self):
        return {
            "userid": "acct:test@localhost",
            "text": "text",
            "tags": ["one", "two"],
            "shared": False,
            "target_uri": "http://www.example.com/example.html",
            "groupid": "__world__",
            "references": [],
            "target_selectors": ["selector_one", "selector_two"],
            "document": {"document_uri_dicts": [], "document_meta_dicts": []},
        }


@pytest.mark.usefixtures("models", "update_document_metadata")
class TestUpdateAnnotation(object):
    def test_it_gets_the_annotation_model(
        self, pyramid_request, annotation_data, group_service, models
    ):
        storage.update_annotation(
            pyramid_request, "test_annotation_id", annotation_data, group_service
        )

        pyramid_request.db.query.assert_called_once_with(models.Annotation)
        pyramid_request.db.query.return_value.get.assert_called_once_with(
            "test_annotation_id"
        )

    def test_it_adds_new_extras(self, pyramid_request, annotation_data, group_service):
        annotation = pyramid_request.db.query.return_value.get.return_value
        annotation.extra = {}
        annotation_data["extra"] = {"foo": "bar"}

        storage.update_annotation(
            pyramid_request, "test_annotation_id", annotation_data, group_service
        )

        assert annotation.extra == {"foo": "bar"}

    def test_it_overwrites_existing_extras(
        self, pyramid_request, annotation_data, group_service
    ):
        annotation = pyramid_request.db.query.return_value.get.return_value
        annotation.extra = {"foo": "original_value"}
        annotation_data["extra"] = {"foo": "new_value"}

        storage.update_annotation(
            pyramid_request, "test_annotation_id", annotation_data, group_service
        )

        assert annotation.extra == {"foo": "new_value"}

    def test_it_does_not_change_extras_that_are_not_sent(
        self, pyramid_request, annotation_data, group_service
    ):
        annotation = pyramid_request.db.query.return_value.get.return_value
        annotation.extra = {"one": 1, "two": 2}
        annotation_data["extra"] = {"two": 22}

        storage.update_annotation(
            pyramid_request, "test_annotation_id", annotation_data, group_service
        )

        assert annotation.extra["one"] == 1

    def test_it_does_not_change_extras_if_none_are_sent(
        self, pyramid_request, annotation_data, group_service
    ):
        annotation = pyramid_request.db.query.return_value.get.return_value
        annotation.extra = {"one": 1, "two": 2}
        assert not annotation_data.get("extra")

        storage.update_annotation(
            pyramid_request, "test_annotation_id", annotation_data, group_service
        )

        assert annotation.extra == {"one": 1, "two": 2}

    def test_it_changes_the_updated_timestamp(
        self, annotation_data, pyramid_request, datetime, group_service
    ):
        annotation = storage.update_annotation(
            pyramid_request, "test_annotation_id", annotation_data, group_service
        )

        assert annotation.updated == datetime.utcnow()

    def test_it_updates_the_annotation(
        self, annotation_data, pyramid_request, group_service
    ):
        annotation = pyramid_request.db.query.return_value.get.return_value

        storage.update_annotation(
            pyramid_request, "test_annotation_id", annotation_data, group_service
        )

        for key, value in annotation_data.items():
            assert getattr(annotation, key) == value

    def test_it_raises_if_missing_group(
        self, annotation_data, pyramid_request, group_service
    ):
        group_service.find.return_value = None

        with pytest.raises(ValidationError) as exc:
            storage.update_annotation(
                pyramid_request, "test_annotation_id", annotation_data, group_service
            )

        assert str(exc.value).startswith("group: ")

    def test_it_allows_when_group_scope_matches(
        self, annotation_data, pyramid_request, group_service, scoped_open_group, models
    ):
        # This target URI matches at least one of the scopes for the group
        # it will go into...
        annotation_data["target_uri"] = "http://www.foo.com/baz/ding.html"

        # this should not raise
        annotation = storage.update_annotation(
            pyramid_request, "test_annotation_id", annotation_data, group_service
        )

        assert annotation == pyramid_request.db.query.return_value.get.return_value

    def test_it_raises_when_group_scope_mismatch(
        self, annotation_data, pyramid_request, group_service, scoped_open_group
    ):
        # This target URI does not match any of the group's defined scopes
        annotation_data["target_uri"] = "http://www.bar.com/baz/ding.html"
        group_service.find.return_value = scoped_open_group

        with pytest.raises(ValidationError) as exc:
            storage.update_annotation(
                pyramid_request, "test_annotation_id", annotation_data, group_service
            )

        assert str(exc.value).startswith("group scope: ")

    def test_it_allows_scope_mismatch_when_enforce_scope_is_False(
        self, annotation_data, pyramid_request, group_service, scoped_open_group
    ):
        scoped_open_group.enforce_scope = False
        group_service.find.return_value = scoped_open_group
        # This target URI is not within any of the group's defined scopes
        annotation_data["target_uri"] = "http://www.bar.com/baz/ding.html"

        # This will not raise because ``enforce_scope`` is set to False for the
        # annotation's group
        annotation = storage.update_annotation(
            pyramid_request, "test_annotation_id", annotation_data, group_service
        )

        assert annotation == pyramid_request.db.query.return_value.get.return_value

    def test_it_allows_group_scope_when_no_target_uri(
        self, annotation_data, pyramid_request, group_service, scoped_open_group
    ):
        annotation_data.pop("target_uri")
        group_service.find.return_value = scoped_open_group

        # this should not raise
        annotation = storage.update_annotation(
            pyramid_request, "test_annotation_id", annotation_data, group_service
        )

        assert annotation == pyramid_request.db.query.return_value.get.return_value

    def test_it_updates_the_document_metadata_from_the_annotation(
        self,
        annotation_data,
        pyramid_request,
        datetime,
        update_document_metadata,
        group_service,
    ):
        annotation = pyramid_request.db.query.return_value.get.return_value
        annotation_data["document"][
            "document_meta_dicts"
        ] = mock.sentinel.document_meta_dicts
        annotation_data["document"][
            "document_uri_dicts"
        ] = mock.sentinel.document_uri_dicts

        storage.update_annotation(
            pyramid_request, "test_annotation_id", annotation_data, group_service
        )

        update_document_metadata.assert_called_once_with(
            pyramid_request.db,
            annotation.target_uri,
            mock.sentinel.document_meta_dicts,
            mock.sentinel.document_uri_dicts,
            updated=datetime.utcnow(),
        )

    def test_it_updates_the_annotations_document_id(
        self, annotation_data, pyramid_request, update_document_metadata, group_service
    ):
        annotation = pyramid_request.db.query.return_value.get.return_value
        document = mock.Mock()
        update_document_metadata.return_value = document

        storage.update_annotation(
            pyramid_request, "test_annotation_id", annotation_data, group_service
        )
        assert annotation.document == document

    def test_it_returns_the_annotation(
        self, annotation_data, pyramid_request, group_service
    ):
        annotation = storage.update_annotation(
            pyramid_request, "test_annotation_id", annotation_data, group_service
        )

        assert annotation == pyramid_request.db.query.return_value.get.return_value

    def test_it_does_not_crash_if_no_document_in_data(
        self, pyramid_request, group_service
    ):
        storage.update_annotation(
            pyramid_request, "test_annotation_id", {}, group_service
        )

    def test_it_does_not_call_update_document_meta_if_no_document_in_data(
        self, pyramid_request, update_document_metadata, group_service
    ):

        storage.update_annotation(
            pyramid_request, "test_annotation_id", {}, group_service
        )

        assert not update_document_metadata.called

    @pytest.fixture
    def annotation_data(self):
        return {
            "userid": "acct:test@localhost",
            "text": "text",
            "tags": ["one", "two"],
            "shared": False,
            "target_uri": "http://www.example.com/example.html",
            "groupid": "__world__",
            "references": [],
            "target_selectors": ["selector_one", "selector_two"],
            "document": {"document_uri_dicts": [], "document_meta_dicts": []},
            "extra": {},
        }


@pytest.fixture
def fetch_annotation(patch):
    return patch("h.storage.fetch_annotation")


@pytest.fixture
def models(patch):
    models = patch("h.storage.models", autospec=False)
    models.Annotation.return_value.is_reply = False
    return models


@pytest.fixture
def update_document_metadata(patch):
    return patch("h.storage.update_document_metadata")


@pytest.fixture
def session(db_session):
    session = mock.Mock(spec=db_session)
    session.query.return_value.get.return_value.extra = {}
    return session


@pytest.fixture
def pyramid_request(session, pyramid_request):
    pyramid_request.db = session
    return pyramid_request


@pytest.fixture
def datetime(patch):
    return patch("h.storage.datetime")


@pytest.fixture
def scoped_open_group(factories):
    scope = factories.GroupScope(scope="http://www.foo.com")
    return factories.OpenGroup(scopes=[scope])


@pytest.fixture
def group_service(pyramid_config, factories):
    open_group = factories.OpenGroup()
    group_service = mock.Mock(spec_set=["find"])
    group_service.find.return_value = open_group
    pyramid_config.register_service(group_service, iface="h.interfaces.IGroupService")
    return group_service
