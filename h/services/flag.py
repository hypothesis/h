import sqlalchemy as sa

from h.models import Flag


class FlagService:
    def __init__(self, session):
        self._session = session

    def flagged(self, user, annotation):
        """
        Check if a given user has flagged a given annotation.

        :param user: The user to check for a flag.
        :type user: h.models.User

        :param annotation: The annotation to check for a flag.
        :type annotation: h.models.Annotation

        :returns: True/False depending on the existence of a flag.
        :rtype: bool
        """
        query = self._session.query(Flag).filter_by(user=user, annotation=annotation)
        return query.count() > 0

    def all_flagged(self, user, annotation_ids):
        """
        Check which of the given annotation IDs the given user has flagged.

        :param user: The user to check for a flag.
        :type user: h.models.User

        :param annotation_ids: The IDs of the annotations to check.
        :type annotation_ids: sequence of unicode

        :returns The subset of the IDs that the given user has flagged.
        :rtype set of unicode
        """
        # SQLAlchemy doesn't behave in the way we might expect when handed an
        # `in_` condition with an empty sequence
        if not annotation_ids:
            return set()

        query = self._session.query(Flag.annotation_id).filter(
            Flag.annotation_id.in_(annotation_ids), Flag.user == user
        )

        return {f.annotation_id for f in query}

    def create(self, user, annotation):
        """
        Create a flag for the given user and annotation.

        We enforce the uniqueness of a flag, meaning one user can only
        flag one annotation once. This method first checks if the annotation
        is already flagged by the user, if that is the case, then this
        is a no-op.

        :param user: The user flagging the annotation.
        :type user: h.models.User

        :param annotation: The annotation to be flagged.
        :type annotation: h.models.Annotation
        """
        if self.flagged(user, annotation):
            return

        flag = Flag(user=user, annotation=annotation)
        self._session.add(flag)

    def flag_count(self, annotation):
        """
        Return the number of times a given annotation has been flagged.

        :param annotation: The annotation to check for flags.
        :type annotation: h.models.Annotation

        :returns: The number of times the annotation has been flagged.
        :rtype: int
        """
        return (
            self._session.query(sa.func.count(Flag.id))
            .filter(Flag.annotation_id == annotation.id)
            .scalar()
        )

    def flag_counts(self, annotation_ids):
        """
        Return flag counts for a batch of annotations.

        :param annotation_ids: The IDs of the annotations to check.
        :type annotation_ids: sequence of unicode

        :returns: A map of annotation IDs to flag counts.
        :rtype: dict[unicode, int]
        """
        if not annotation_ids:
            return {}

        query = (
            self._session.query(
                sa.func.count(Flag.id).label("flag_count"), Flag.annotation_id
            )
            .filter(Flag.annotation_id.in_(annotation_ids))
            .group_by(Flag.annotation_id)
        )

        flag_counts = {f.annotation_id: f.flag_count for f in query}
        missing_ids = set(annotation_ids) - set(flag_counts.keys())
        flag_counts.update({id_: 0 for id_ in missing_ids})
        return flag_counts


def flag_service_factory(_context, request):
    return FlagService(request.db)
