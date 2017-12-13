# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest
from mock import Mock, call

from h.events import AnnotationEvent
from h.models import Annotation, Document, Group
from h.services.delete_user import (
    UserDeleteError,
    delete_user_service_factory,
)


class TestDeleteUserService(object):

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

    def test_delete_user_removes_groups_if_no_collaborators(self, db_session, group_with_two_users, pyramid_request, svc):
        pyramid_request.db = db_session
        (group, user, other_user, user_ann, other_user_ann) = group_with_two_users
        db_session.delete(other_user_ann)

        svc.delete(user)

        assert group in db_session.deleted

    def test_delete_user_fails_if_groups_have_collaborators(self, db_session, group_with_two_users, pyramid_request, svc):
        pyramid_request.db = db_session
        (group, user, other_user, user_ann, other_user_ann) = group_with_two_users

        with pytest.raises(UserDeleteError):
            svc.delete(user)

    @pytest.fixture
    def svc(self, db_session, pyramid_request):
        pyramid_request.db = db_session
        return delete_user_service_factory({}, pyramid_request)


@pytest.fixture
def pyramid_request(pyramid_request):
    pyramid_request.notify_after_commit = Mock()
    return pyramid_request


@pytest.fixture
def api_storage(patch):
    return patch('h.services.delete_user.storage')


@pytest.fixture
def group_with_two_users(db_session, factories):
    """
    Create a group with two members and an annotation created by each.
    """
    user = factories.User()
    other_user = factories.User()

    group = Group(authority=user.authority, creator=user, members=[user, other_user],
                  name='test', pubid='group_with_two_users')
    db_session.add(group)

    doc = Document(web_uri='https://example.org')
    user_ann = Annotation(userid=user.userid, groupid=group.pubid, document=doc)
    other_user_ann = Annotation(userid=other_user.userid, groupid=group.pubid,
                                document=doc)
    db_session.add(user_ann)
    db_session.add(other_user_ann)
    db_session.flush()

    return (group, user, other_user, user_ann, other_user_ann)
