# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest
from mock import Mock, call

from h.events import AnnotationEvent
from h.services.delete_user import (
    UserDeleteError,
    delete_user_service_factory,
)

delete_user_fixtures = pytest.mark.usefixtures('api_storage',
                                               'user_created_no_groups')


@delete_user_fixtures
class TestDeleteUserService(object):

    def test_delete_raises_when_group_creator(self, Group, svc): # noqa N803
        user = Mock()

        Group.created_by.return_value.count.return_value = 10

        with pytest.raises(UserDeleteError):
            svc.delete(user)

    def test_delete_disassociate_group_memberships(self, factories, svc):
        user = factories.User()

        svc.delete(user)

        assert user.groups == []

    def test_delete_deletes_annotations(self, api_storage, factories, pyramid_request, svc):
        user = factories.User(username='bob')
        anns = [factories.Annotation(userid=user.userid),
                factories.Annotation(userid=user.userid)]

        svc.delete(user)

        api_storage.delete_annotation.assert_has_calls([
            call(pyramid_request.db, anns[0].id),
            call(pyramid_request.db, anns[1].id),
        ], any_order=True)

    def test_delete_publishes_event(self, api_storage, db_session, factories,
                                    matchers, pyramid_request, svc):
        user = factories.User()
        ann = factories.Annotation(userid=user.userid)

        svc.delete(user)

        expected_event = AnnotationEvent(pyramid_request, ann.id, 'delete')
        actual_event = pyramid_request.notify_after_commit.call_args[0][0]
        assert (expected_event.request, expected_event.annotation_id, expected_event.action) == \
               (actual_event.request, actual_event.annotation_id, actual_event.action)

    def test_delete_deletes_user(self, db_session, factories, pyramid_request, svc):
        user = factories.User()

        svc.delete(user)

        assert user in db_session.deleted

    @pytest.fixture
    def svc(self, db_session, pyramid_request):
        pyramid_request.db = db_session
        return delete_user_service_factory({}, pyramid_request)


@pytest.fixture
def user_created_no_groups(Group): # noqa N803
    # By default, pretend that all users are the creators of 0 groups.
    Group.created_by.return_value.count.return_value = 0


@pytest.fixture
def pyramid_request(pyramid_request):
    pyramid_request.notify_after_commit = Mock()
    return pyramid_request


@pytest.fixture
def api_storage(patch):
    return patch('h.services.delete_user.storage')


@pytest.fixture
def Group(patch): # noqa N802
    return patch('h.services.delete_user.Group')
