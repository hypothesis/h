# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import mock
import pytest

from h.services.delete_group import (
    delete_group_service_factory,
    DeleteGroupService,
    DeletePublicGroupError,
)
from h.services.delete_annotation import DeleteAnnotationService


@pytest.mark.usefixtures("delete_annotation_service")
class TestDeleteGroupService(object):
    def test_delete_does_not_delete_public_group(self, svc, db_session, factories):
        group = factories.Group()
        group.pubid = "__world__"

        with pytest.raises(DeletePublicGroupError):
            svc.delete(group)

    def test_delete_deletes_group(self, svc, db_session, factories):
        group = factories.Group()

        svc.delete(group)

        assert group in db_session.deleted

    def test_delete_deletes_annotations(
        self, svc, factories, pyramid_request, delete_annotation_service
    ):
        group = factories.Group()
        annotations = [
            factories.Annotation(groupid=group.pubid),
            factories.Annotation(groupid=group.pubid),
        ]

        svc.delete(group)

        delete_annotation_service.delete.assert_has_calls(
            [mock.call(annotations[0]), mock.call(annotations[1])], any_order=True
        )

    def test_delete_group_factory(self, pyramid_request):
        svc = delete_group_service_factory(None, pyramid_request)

        assert isinstance(svc, DeleteGroupService)


@pytest.fixture
def svc(db_session, pyramid_request):
    pyramid_request.db = db_session
    return delete_group_service_factory({}, pyramid_request)


@pytest.fixture
def delete_annotation_service(pyramid_config):
    service = mock.create_autospec(
        DeleteAnnotationService, spec_set=True, instance=True
    )
    pyramid_config.register_service(service, name="delete_annotation")
    return service
