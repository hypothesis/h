# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest
import mock
import sqlalchemy

from h.models import Annotation, Document
from h.services.delete_user import delete_user_service_factory
from h.services.annotation_delete import AnnotationDeleteService


@pytest.mark.usefixtures("annotation_delete_service")
class TestDeleteUserService(object):
    def test_delete_disassociate_group_memberships(self, factories, svc):
        user = factories.User()

        svc.delete(user)

        assert user.groups == []

    def test_delete_deletes_annotations(
        self, factories, pyramid_request, svc, annotation_delete_service
    ):
        user = factories.User(username="bob")
        anns = [
            factories.Annotation(userid=user.userid),
            factories.Annotation(userid=user.userid),
        ]

        svc.delete(user)

        annotation_delete_service.delete.assert_has_calls(
            [mock.call(anns[0]), mock.call(anns[1])], any_order=True
        )

    def test_delete_deletes_user(self, db_session, factories, pyramid_request, svc):
        user = factories.User()

        svc.delete(user)

        assert user in db_session.deleted

    def test_delete_user_removes_groups_if_no_collaborators(
        self, db_session, group_with_two_users, pyramid_request, svc
    ):
        pyramid_request.db = db_session
        (group, creator, member, creator_ann, member_ann) = group_with_two_users
        db_session.delete(member_ann)

        svc.delete(creator)

        assert sqlalchemy.inspect(group).was_deleted

    def test_creator_is_none_if_groups_have_collaborators(
        self, db_session, group_with_two_users, pyramid_request, svc
    ):
        pyramid_request.db = db_session
        (group, creator, member, creator_ann, member_ann) = group_with_two_users

        svc.delete(creator)

        assert group.creator is None

    def test_delete_user_removes_only_groups_created_by_user(
        self, db_session, group_with_two_users, pyramid_request, svc
    ):
        pyramid_request.db = db_session
        (group, creator, member, creator_ann, member_ann) = group_with_two_users

        svc.delete(member)

        assert group not in db_session.deleted

    @pytest.fixture
    def svc(self, db_session, pyramid_request):
        pyramid_request.db = db_session
        return delete_user_service_factory({}, pyramid_request)


@pytest.fixture
def pyramid_request(pyramid_request):
    pyramid_request.notify_after_commit = mock.Mock()
    return pyramid_request


@pytest.fixture
def group_with_two_users(db_session, factories):
    """
    Create a group with two members and an annotation created by each.
    """
    creator = factories.User()
    member = factories.User()

    group = factories.Group(
        authority=creator.authority, creator=creator, members=[creator, member]
    )

    doc = Document(web_uri="https://example.org")
    creator_ann = Annotation(userid=creator.userid, groupid=group.pubid, document=doc)
    member_ann = Annotation(userid=member.userid, groupid=group.pubid, document=doc)

    db_session.add(creator_ann)
    db_session.add(member_ann)
    db_session.flush()

    return (group, creator, member, creator_ann, member_ann)


@pytest.fixture
def annotation_delete_service(pyramid_config):
    service = mock.create_autospec(
        AnnotationDeleteService, spec_set=True, instance=True
    )
    pyramid_config.register_service(service, name="annotation_delete")
    return service
