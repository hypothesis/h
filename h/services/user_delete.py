import sqlalchemy as sa

from h.models import Annotation, Group, User
from h.services.annotation_delete import AnnotationDeleteService


class UserDeleteService:
    def __init__(
        self,
        db_session: sa.orm.Session,
        annotation_delete_service: AnnotationDeleteService,
    ):
        self._db = db_session
        self._annotation_delete_service = annotation_delete_service

    def delete_user(self, user: User):
        """
        Delete a user with all their group memberships and annotations.

        If a user owns groups with collaborators, meaning there are annotations
        in the group that have been made by other users, the user is unassigned
        as creator but the group persists.
        """

        # Delete all annotations
        self._annotation_delete_service.delete_annotations(
            annotations=self._db.query(Annotation).filter_by(userid=user.userid).all()
        )

        # Delete or remove our link to groups we've created
        for group, annotations_by_other_users in self._db.execute(
            sa.select([Group, sa.func.count(Annotation.id)])
            .where(Group.creator == user)
            .outerjoin(
                Annotation,
                sa.and_(
                    Annotation.groupid == Group.pubid, Annotation.userid != user.userid
                ),
            )
            .group_by(Group.id)
        ):
            if annotations_by_other_users:
                group.creator = None
            else:
                self._db.delete(group)

        self._db.delete(user)


def service_factory(_context, request):
    return UserDeleteService(
        db_session=request.db,
        annotation_delete_service=request.find_service(name="annotation_delete"),
    )
