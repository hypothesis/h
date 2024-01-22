import sqlalchemy as sa

from h.models import Annotation, Flag, User


class FlagService:
    def __init__(self, session):
        self._session = session

        self._flagged_cache = {}
        self._flag_count_cache = {}

    def create(self, user: User, annotation: Annotation):
        """
        Create a flag for the given user and annotation.

        We enforce the uniqueness of a flag, meaning one user can only
        flag one annotation once. This method first checks if the annotation
        is already flagged by the user, if that is the case, then this
        is a no-op.

        :param user: The user flagging the annotation.
        :param annotation: The annotation to be flagged.
        """
        if self.flagged(user, annotation):
            return

        self._session.add(Flag(user=user, annotation=annotation))

    def flagged(self, user: User, annotation: Annotation):
        """
        Check if a given user has flagged a given annotation.

        You can make this more efficient for a large batch of annotations by
        calling `all_flagged()` which will prime a cache of results.

        :param user: The user to check for a flag.
        :param annotation: The annotation to check for a flag.
        :returns: True/False depending on the existence of a flag.
        """
        if not user or not annotation:
            return False

        # This cache can be primed by calling `all_flagged()`
        key = user.id, annotation.id
        if key in self._flagged_cache:
            return self._flagged_cache[key]

        is_flagged = bool(
            self._session.query(Flag)
            .filter_by(user=user, annotation=annotation)
            .first()
        )
        self._flagged_cache[key] = is_flagged

        return is_flagged

    def all_flagged(self, user: User, annotation_ids):
        """
        Check which of the given annotation IDs the given user has flagged.

        :param user: The user to check for a flag.
        :param annotation_ids: The IDs of the annotations to check.
        :returns The subset of the IDs that the given user has flagged.
        """

        # SQLAlchemy doesn't behave in the way we might expect when handed an
        # `in_` condition with an empty sequence
        if not annotation_ids or not user:
            return set()

        query = self._session.query(Flag.annotation_id).filter(
            Flag.annotation_id.in_(annotation_ids), Flag.user == user
        )

        flagged_ids = {f.annotation_id for f in query}

        # Fill out the cache, so we can make use of it in flagged()
        for annotation_id in annotation_ids:
            self._flagged_cache[(user.id, annotation_id)] = annotation_id in flagged_ids

        return {f.annotation_id for f in query}

    def flag_count(self, annotation: Annotation):
        """
        Return the number of times a given annotation has been flagged.

        You can make this more efficient for a large batch of annotations by
        calling `flag_counts()` which will prime a cache of results.

        :param annotation: The annotation to check for flags.
        :returns: The number of times the annotation has been flagged.
        """

        if not annotation:
            return 0

        # This cache can be primed by calling `flag_counts()`
        if annotation.id in self._flag_count_cache:
            return self._flag_count_cache[annotation.id]

        self._flag_count_cache[annotation.id] = flag_count = (
            # pylint:disable=not-callable
            self._session.query(sa.func.count(Flag.id))
            .filter(Flag.annotation_id == annotation.id)
            .scalar()
        )

        return flag_count

    def flag_counts(self, annotation_ids):
        """
        Return flag counts for a batch of annotations.

        :param annotation_ids: The IDs of the annotations to check.
        :returns: A map of annotation IDs to flag counts.
        """
        if not annotation_ids:
            return {}

        query = (
            self._session.query(
                # pylint:disable=not-callable
                sa.func.count(Flag.id).label("flag_count"),
                Flag.annotation_id,
            )
            .filter(Flag.annotation_id.in_(annotation_ids))
            .group_by(Flag.annotation_id)
        )

        flag_counts = {f.annotation_id: f.flag_count for f in query}
        missing_ids = set(annotation_ids) - set(flag_counts.keys())
        flag_counts.update({id_: 0 for id_ in missing_ids})

        # Prime the cache for `flag_count()`
        self._flag_count_cache.update(flag_counts)

        return flag_counts


def flag_service_factory(_context, request):
    return FlagService(request.db)
