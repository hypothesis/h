from unittest.mock import sentinel

import pytest
import sqlalchemy
from h_matchers import Any

from h.models import GroupMembership, Token, UserDeletion
from h.services.user_delete import UserDeleteService, service_factory


class TestDeleteUserService:
    @pytest.mark.usefixtures("user_developer_token", "user_oauth2_token")
    def test_it(
        self,
        svc,
        db_session,
        annotation_delete_service,
        user,
        requested_by,
        created_group,
        joined_group,
        user_annotations,
        other_developer_token,
        other_oauth2_token,
    ):
        svc.delete_user(user, requested_by, "test_tag")

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
        assert (
            db_session.scalars(sqlalchemy.select(Token)).all()
            == Any.list.containing([other_developer_token, other_oauth2_token]).only()
        )
        assert (
            db_session.scalars(sqlalchemy.select(UserDeletion)).all()
            == Any.list.containing(
                [
                    Any.instance_of(UserDeletion).with_attrs(
                        {
                            "userid": user.userid,
                            "requested_by": requested_by.userid,
                            "tag": "test_tag",
                            "registered_date": user.registered_date,
                            "num_annotations": len(user_annotations),
                        }
                    )
                ]
            ).only()
        )

    def test_it_doesnt_delete_groups_others_have_annotated_in(
        self, svc, factories, user, requested_by, member, created_group
    ):
        factories.Annotation(userid=member.userid, groupid=created_group.pubid)

        svc.delete_user(user, requested_by, "test_tag")

        # Check we don't delete groups which other people have annotated in
        assert not sqlalchemy.inspect(created_group).was_deleted
        # But that we are removed as the creator
        assert not created_group.creator

    @pytest.fixture
    def user(self, factories):
        """Return the user who will be deleted."""
        return factories.User()

    @pytest.fixture
    def requested_by(self, factories):
        """Return the user who will be requesting the user deletion."""
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
    def user_developer_token(self, user, factories):
        return factories.DeveloperToken(user=user)

    @pytest.fixture
    def user_oauth2_token(self, user, factories):
        return factories.OAuth2Token(user=user)

    @pytest.fixture
    def other_developer_token(self, factories):
        return factories.DeveloperToken()

    @pytest.fixture
    def other_oauth2_token(self, factories):
        return factories.OAuth2Token()

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
