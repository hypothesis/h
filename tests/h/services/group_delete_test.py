from unittest import mock

import pytest

from h.services.annotation_delete import AnnotationDeleteService
from h.services.group_delete import (
    DeletePublicGroupError,
    GroupDeleteService,
    service_factory,
)


@pytest.mark.usefixtures("annotation_delete_service")
class TestGroupDeleteService:
    def test_it_does_not_delete_public_group(self, svc, factories):
        group = factories.Group()
        group.pubid = "__world__"

        with pytest.raises(DeletePublicGroupError):
            svc.delete(group)

    def test_it_deletes_group(self, svc, db_session, factories):
        group = factories.Group()

        svc.delete(group)

        assert group in db_session.deleted

    def test_it_deletes_annotations(self, svc, factories, annotation_delete_service):
        group = factories.Group()
        annotations = [
            factories.Annotation(groupid=group.pubid).id,
            factories.Annotation(groupid=group.pubid).id,
        ]

        svc.delete(group)

        deleted_anns = [
            ann.id
            for ann in annotation_delete_service.delete_annotations.call_args[0][0]
        ]
        assert sorted(deleted_anns) == sorted(annotations)


@pytest.mark.usefixtures("annotation_delete_service")
class TestServiceFactory:
    def test_it_returns_group_delete_service_instance(self, pyramid_request):
        svc = service_factory(None, pyramid_request)

        assert isinstance(svc, GroupDeleteService)


@pytest.fixture
def svc(db_session, pyramid_request):
    pyramid_request.db = db_session
    return service_factory({}, pyramid_request)


@pytest.fixture
def annotation_delete_service(pyramid_config):
    service = mock.create_autospec(
        AnnotationDeleteService, spec_set=True, instance=True
    )
    pyramid_config.register_service(service, name="annotation_delete")
    return service
