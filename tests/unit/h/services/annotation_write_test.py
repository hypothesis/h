from datetime import datetime, timedelta
from unittest.mock import Mock, patch, sentinel

import pytest
from h_matchers import Any

from h.models import Annotation, AnnotationModeration, AnnotationSlim, User
from h.schemas import ValidationError
from h.security import Permission
from h.services.annotation_write import AnnotationWriteService, service_factory
from h.traversal.group import GroupContext


class TestAnnotationWriteService:
    def test_create_annotation(
        self,
        svc,
        create_data,
        factories,
        update_document_metadata,
        search_index,
        annotation_read_service,
        _validate_group,
        db_session,
    ):
        root_annotation = factories.Annotation()
        annotation_read_service.get_annotation_by_id.return_value = root_annotation
        create_data["references"] = [root_annotation.id, factories.Annotation().id]
        create_data["groupid"] = "IGNORED"
        update_document_metadata.return_value = factories.Document()

        anno = svc.create_annotation(create_data)

        annotation_read_service.get_annotation_by_id.assert_called_once_with(
            root_annotation.id
        )
        _validate_group.assert_called_once_with(anno)
        # pylint: disable=protected-access
        search_index._queue.add_by_id.assert_called_once_with(
            anno.id, tag="storage.create_annotation", schedule_in=60
        )

        assert anno == Any.instance_of(Annotation).with_attrs(
            {
                "userid": create_data["userid"],
                "groupid": root_annotation.groupid,
                "target_uri": create_data["target_uri"],
                "references": create_data["references"],
                "document": update_document_metadata.return_value,
            }
        )
        self.assert_annotation_slim(db_session, anno)

    def test_create_annotation_with_metadata(
        self, svc, create_data, annotation_metadata_service, factories
    ):
        group = factories.Group()
        create_data["references"] = None
        create_data["groupid"] = group.pubid
        create_data["metadata"] = sentinel.metadata

        result = svc.create_annotation(create_data)

        annotation_metadata_service.set.assert_called_once_with(
            result, sentinel.metadata
        )

    def test_create_annotation_as_root(
        self, svc, create_data, factories, annotation_read_service
    ):
        group = factories.Group()
        create_data["references"] = None
        create_data["groupid"] = group.pubid

        result = svc.create_annotation(create_data)

        annotation_read_service.get_annotation_by_id.assert_not_called()
        assert result.groupid == group.pubid

    def test_create_annotation_with_invalid_parent(
        self, svc, create_data, annotation_read_service
    ):
        create_data["references"] = ["NOPE!"]
        annotation_read_service.get_annotation_by_id.return_value = None

        with pytest.raises(ValidationError):
            svc.create_annotation(create_data)

    def test_update_annotation(
        self,
        svc,
        db_session,
        annotation,
        update_document_metadata,
        search_index,
        _validate_group,
    ):
        then = datetime.now() - timedelta(days=1)
        annotation.extra = {"key": "value"}
        annotation.updated = then

        anno = svc.update_annotation(
            annotation,
            {
                "target_uri": "new_target_uri",
                "text": "new_text",
                "extra": {"extra_key": "extra_value"},
                "document": {
                    "document_meta_dicts": {"meta": 1},
                    "document_uri_dicts": {"uri": 1},
                },
            },
            update_timestamp=True,
            enforce_write_permission=sentinel.enforce_write_permission,
        )

        _validate_group.assert_called_once_with(
            annotation, enforce_write_permission=sentinel.enforce_write_permission
        )
        update_document_metadata.assert_called_once_with(
            db_session,
            anno.target_uri,
            {"meta": 1},
            {"uri": 1},
            updated=anno.updated,
        )

        # pylint: disable=protected-access
        search_index._queue.add_by_id.assert_called_once_with(
            annotation.id, tag="storage.update_annotation", schedule_in=60, force=False
        )
        assert anno.document == update_document_metadata.return_value
        assert anno.target_uri == "new_target_uri"
        assert anno.text == "new_text"
        assert anno.updated > then
        assert anno.extra == {"key": "value", "extra_key": "extra_value"}
        self.assert_annotation_slim(db_session, anno)

    def test_update_annotation_with_non_defaults(self, svc, annotation, search_index):
        then = datetime.now() - timedelta(days=1)
        annotation.updated = then

        result = svc.update_annotation(
            annotation, {}, update_timestamp=False, reindex_tag="custom_tag"
        )

        # pylint: disable=protected-access
        search_index._queue.add_by_id.assert_called_once_with(
            Any(), tag="custom_tag", schedule_in=Any(), force=True
        )
        assert result.updated == then

    def test_update_annotation_with_metadata(
        self, svc, annotation, annotation_metadata_service
    ):
        result = svc.update_annotation(
            annotation,
            {"metadata": sentinel.metadata},
            update_timestamp=False,
            reindex_tag="custom_tag",
        )

        annotation_metadata_service.set.assert_called_once_with(
            result, sentinel.metadata
        )

    def test__validate_group_with_no_group(self, svc, annotation):
        annotation.group = None

        with pytest.raises(ValidationError):
            svc._validate_group(annotation)  # pylint: disable=protected-access

    def test__validate_group_with_no_permission(self, svc, annotation, has_permission):
        has_permission.return_value = False

        with pytest.raises(ValidationError):
            svc._validate_group(annotation)  # pylint: disable=protected-access

        has_permission.assert_called_once_with(
            Permission.Group.WRITE, context=GroupContext(annotation.group)
        )

    def test__validate_group_with_no_permission_and_checking_disabled(
        self, svc, annotation, has_permission
    ):
        has_permission.return_value = False

        # pylint: disable=protected-access
        svc._validate_group(annotation, enforce_write_permission=False)

        has_permission.assert_not_called()

    @pytest.mark.parametrize("enforce_scope", (True, False))
    @pytest.mark.parametrize("matching_scope", (True, False))
    @pytest.mark.parametrize("has_scopes", (True, False))
    def test__validate_group_with_url_not_in_scopes(
        self, svc, annotation, factories, enforce_scope, matching_scope, has_scopes
    ):
        annotation.group.enforce_scope = enforce_scope
        annotation.target_uri = "http://scope" if matching_scope else "http://MISMATCH"
        if has_scopes:
            annotation.group.scopes = [factories.GroupScope(scope="http://scope")]

        if enforce_scope and has_scopes and not matching_scope:
            with pytest.raises(ValidationError):
                svc._validate_group(annotation)  # pylint: disable=protected-access
        else:
            svc._validate_group(annotation)  # pylint: disable=protected-access

    def test_hide_hides_the_annotation(self, annotation, svc):
        annotation.moderation = None

        svc.hide(annotation)

        assert annotation.is_hidden

    def test_hide_does_not_modify_an_already_hidden_annotation(self, annotation, svc):
        moderation = AnnotationModeration()
        annotation.moderation = moderation

        svc.hide(annotation)

        assert annotation.is_hidden
        # It's the same one not a new one
        assert annotation.moderation == moderation

    def test_unhide(self, annotation, svc):
        moderation = AnnotationModeration()
        annotation.moderation = moderation

        svc.unhide(annotation)

        assert not annotation.is_hidden

    @pytest.fixture
    def create_data(self, factories):
        user = factories.User()

        return {
            "userid": user.userid,
            "target_uri": "http://example.com/target",
            "document": {
                "document_uri_dicts": sentinel.uri_dicts,
                "document_meta_dicts": sentinel.document_dicts,
            },
        }

    @pytest.fixture
    def annotation(self, factories):
        user = factories.User()
        return factories.Annotation(userid=user.userid)

    @pytest.fixture
    def has_permission(self):
        return Mock(return_value=True)

    @pytest.fixture
    def svc(
        self,
        db_session,
        has_permission,
        search_index,
        annotation_read_service,
        annotation_metadata_service,
    ):
        return AnnotationWriteService(
            db_session=db_session,
            has_permission=has_permission,
            search_index_service=search_index,
            annotation_read_service=annotation_read_service,
            annotation_metadata_service=annotation_metadata_service,
        )

    @pytest.fixture
    def _validate_group(self, svc):
        with patch.object(svc, "_validate_group") as _validate_group:
            yield _validate_group

    @pytest.fixture(autouse=True)
    def update_document_metadata(self, patch, factories):
        update_document_metadata = patch(
            "h.services.annotation_write.update_document_metadata"
        )
        update_document_metadata.return_value = factories.Document()
        return update_document_metadata

    def assert_annotation_slim(self, db_session, annotation):
        slim = db_session.query(AnnotationSlim).filter_by(pubid=annotation.id).one()

        assert (
            slim.user_id
            == db_session.query(User).filter_by(userid=annotation.userid).one().id
        )
        assert slim.group_id == annotation.group.id
        assert slim.document_id == annotation.document_id
        assert slim.deleted == annotation.deleted


class TestServiceFactory:
    def test_it(
        self,
        pyramid_request,
        AnnotationWriteService,
        search_index,
        annotation_read_service,
        annotation_metadata_service,
    ):
        svc = service_factory(sentinel.context, pyramid_request)

        AnnotationWriteService.assert_called_once_with(
            db_session=pyramid_request.db,
            has_permission=pyramid_request.has_permission,
            search_index_service=search_index,
            annotation_read_service=annotation_read_service,
            annotation_metadata_service=annotation_metadata_service,
        )
        assert svc == AnnotationWriteService.return_value

    @pytest.fixture
    def AnnotationWriteService(self, patch):
        return patch("h.services.annotation_write.AnnotationWriteService")
