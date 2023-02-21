from sqlalchemy import func, select

from h.models import Annotation, AnnotationModeration, User, Group


class EmailDigestsService:
    def __init__(self, db, group_service):
        self.db = db
        self.group_service = group_service

    def get(self, user, since, until):
        groupids = self.group_service.groupids_readable_by(user)

        stmt = (
            select(Group.pubid, Group.authority_provided_id, User.username, func.count(1))
            .join(Annotation, Annotation.groupid == Group.pubid)
            .outerjoin(AnnotationModeration)
            .join(
                User,
                User.username
                == func.split_part(func.split_part(Annotation.userid, "@", 1), ":", 2)
                and User.authority == func.split_part(Annotation.userid, "@", 2),
            )
            .group_by(Group.pubid, Group.authority_provided_id, User.username)
            .where(Annotation.shared.is_(True))
            .where(Annotation.deleted.is_(False))
            .where(Annotation.groupid.in_(groupids))

            # FIXME: This should be annotation.created rather than updated but
            # we need to add an index to created first.
            .where(Annotation.updated > since)
            .where(Annotation.updated <= until)

            .where(AnnotationModeration.id.is_(None))
            .where(User.nipsa.is_(False))
        )

        result = self.db.execute(stmt).all()

        return result


def factory(context, request):
    return EmailDigestsService(
        db=request.db, group_service=request.find_service(name="group")
    )
