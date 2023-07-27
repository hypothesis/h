from unittest import mock
from unittest.mock import sentinel

import pytest
import sqlalchemy
from h_matchers import Any

from h.models import Annotation, Document
from h.services.annotation_delete import AnnotationDeleteService
from h.services.user_delete import UserDeleteService, service_factory


class TestDeleteUserService:
    def test_delete_disassociate_group_memberships(self, svc, factories):
        user = factories.User()

        svc.delete_user(user)

        assert user.groups == []

    def test_delete_deletes_annotations(
        self, svc, factories, annotation_delete_service
    ):
        user = factories.User(username="bob")
        annotations = factories.Annotation.create_batch(2, userid=user.userid)

        svc.delete_user(user)

        annotation_delete_service.delete_annotations.assert_called_once_with(
            Any.iterable.containing(annotations).only()
        )

    def test_delete_deletes_user(self, svc, db_session, factories):
        user = factories.User()

        svc.delete_user(user)

        assert user in db_session.deleted

    def test_delete_user_removes_groups_if_no_collaborators(
        self, svc, db_session, group_with_two_users
    ):
        (group, creator, _, _, member_ann) = group_with_two_users
        db_session.delete(member_ann)

        svc.delete_user(creator)

        assert sqlalchemy.inspect(group).was_deleted

    def test_creator_is_none_if_groups_have_collaborators(
        self, svc, group_with_two_users
    ):
        (group, creator, _, _, _) = group_with_two_users

        svc.delete_user(creator)

        assert group.creator is None

    def test_delete_user_removes_only_groups_created_by_user(
        self, svc, db_session, group_with_two_users
    ):
        (group, _, member, _, _) = group_with_two_users

        svc.delete_user(member)

        assert group not in db_session.deleted

    @pytest.fixture
    def svc(self, db_session, annotation_delete_service):
        return UserDeleteService(
            db_session=db_session, annotation_delete_service=annotation_delete_service
        )


@pytest.fixture
def pyramid_request(pyramid_request):
    pyramid_request.notify_after_commit = mock.Mock()
    return pyramid_request


@pytest.fixture
def group_with_two_users(db_session, factories):
    """Create a group with two members and an annotation created by each."""
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


class TestServiceFactory:
    def test_it(self, pyramid_request, annotation_delete_service, UserDeleteService):
        svc = service_factory(sentinel.context, pyramid_request)

        UserDeleteService.assert_called_once_with(
            db_session=pyramid_request.db,
            annotation_delete_service=annotation_delete_service,
        )
        assert svc == UserDeleteService.return_value

    @pytest.fixture
    def UserDeleteService(self, patch):
        return patch("h.services.user_delete.UserDeleteService")
