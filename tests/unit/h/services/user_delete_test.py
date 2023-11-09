from unittest.mock import sentinel

import pytest
import sqlalchemy
from h_matchers import Any

from h.models import GroupMembership
from h.services.user_delete import UserDeleteService, service_factory


class TestDeleteUserService:
    def test_it(
        self,
        svc,
        db_session,
        annotation_delete_service,
        user,
        created_group,
        joined_group,
        user_annotations,
    ):
        svc.delete_user(user)

        # Check the user was deleted
        assert user in db_session.deleted
        # Check we delete this user's annotations
        annotation_delete_service.delete_annotations.assert_called_once_with(
            Any.iterable.containing(user_annotations).only()
        )
        # Check we delete groups we created, but not ones we joined
        assert sqlalchemy.inspect(created_group).was_deleted
        assert not sqlalchemy.inspect(joined_group).was_deleted
        # Check we remove their group memberships
        assert (
            not db_session.query(GroupMembership)
            .where(GroupMembership.user_id == user.id)
            .all()
        )
        assert (
            not db_session.query(GroupMembership)
            .where(GroupMembership.group_id == created_group.id)
            .all()
        )

    def test_it_doesnt_delete_groups_others_have_annotated_in(
        self, svc, factories, user, member, created_group
    ):
        factories.Annotation(userid=member.userid, groupid=created_group.pubid)

        svc.delete_user(user)

        # Check we don't delete groups which other people have annotated in
        assert not sqlalchemy.inspect(created_group).was_deleted
        # But that we are removed as the creator
        assert not created_group.creator

    @pytest.fixture
    def user(self, factories):
        return factories.User()

    @pytest.fixture
    def member(self, factories):
        return factories.User()

    @pytest.fixture
    def created_group(self, factories, user, member):
        return factories.Group(
            authority=user.authority, creator=user, members=[user, member]
        )

    @pytest.fixture
    def joined_group(self, factories, user, member):
        return factories.Group(
            authority=user.authority, creator=member, members=[user, member]
        )

    @pytest.fixture
    def user_annotations(self, factories, user, created_group, joined_group):
        return [
            factories.Annotation(userid=user.userid, groupid=group.pubid)
            for group in (created_group, joined_group)
        ]

    @pytest.fixture
    def svc(self, db_session, annotation_delete_service):
        return UserDeleteService(
            db_session=db_session, annotation_delete_service=annotation_delete_service
        )


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
