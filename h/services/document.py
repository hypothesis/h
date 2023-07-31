import sqlalchemy as sa

from h.models import Annotation, Document

MAX_DOCUMENT_COUNT = 100


class DocumentService:
    def __init__(self, session):
        self._session = session

    def fetch_by_groupid(self, groupid, userid=None):
        """
        Return documents that have been annotated within a given group.

        Return a list of documents that have at least one annotation visible to
        the user within the group indicated. Results are ordered by last document
        activity, descending (document records are updated any time an annotation
        referencing them is added or updated).

        Right now a simple limit is imposed for performance and usability reasons.

        Note: It is the responsibility of the caller to first verify that the user
        (or anonymous) has read authorization for the group indicated.
        While this method filters out individual annotations that are private
        or not owned by the user, it does not protect access to annotations
        within the group itself.
        """

        is_shared = Annotation.shared.is_(True)
        is_visible_to_user = (
            is_shared if not userid else sa.or_(Annotation.userid == userid, is_shared)
        )

        return (
            self._session.query(Document)
            .join(Annotation)
            .filter(Annotation.groupid == groupid)
            .filter(is_visible_to_user)
            .order_by(Document.updated.desc())
            .limit(MAX_DOCUMENT_COUNT)
            .all()
        )


def document_service_factory(_context, request):
    return DocumentService(session=request.db)
