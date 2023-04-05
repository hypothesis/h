from typing import Iterable, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Query, Session, subqueryload

from h.models import Annotation, DocumentURI
from h.util.uri import normalize


class AnnotationService:
    """A service for storing and retrieving annotations."""

    def __init__(self, db_session: Session):
        self._db = db_session

    def get_annotations_by_id(
        self, ids: List[str], eager_load: Optional[List] = None
    ) -> Iterable[Annotation]:
        """
        Get annotations in the same order as the provided ids.

        :param ids: the list of annotation ids
        :param eager_load: A list of annotation relationships to eager load
            like `Annotation.document`
        """

        if not ids:
            return []

        annotations = self._db.execute(
            self._annotation_search_query(ids=ids, eager_load=eager_load)
        ).scalars()

        return sorted(annotations, key=lambda annotation: ids.index(annotation.id))

    def search_annotations(
        self,
        ids: Optional[List[str]] = None,
        target_uri: Optional[str] = None,
        document_uri: Optional[str] = None,
    ) -> Iterable[Annotation]:
        """
        Search for annotations using information stored in Postgres.

        :param ids: Search by specified annotation ids
        :param target_uri: Search by annotation target URI
        :param document_uri: Search by document URI
        """
        query = self._annotation_search_query(
            ids=ids, document_uri=document_uri, target_uri=target_uri
        )

        return self._db.execute(query).scalars().all()

    @staticmethod
    def _annotation_search_query(
        ids: Optional[List[str]] = None,
        document_uri: Optional[str] = None,
        target_uri: Optional[str] = None,
        eager_load: Optional[List] = None,
    ) -> Query:
        """Create a query for searching for annotations."""

        query = select(Annotation)

        if ids:
            query = query.where(Annotation.id.in_(ids))

        if target_uri:
            query = query.where(
                Annotation.target_uri_normalized == normalize(target_uri)
            )

        if document_uri:
            document_subquery = select(DocumentURI.document_id).where(
                DocumentURI.uri_normalized == normalize(document_uri)
            )
            query = query.where(Annotation.document_id.in_(document_subquery))

        if eager_load:
            query = query.options(subqueryload(*eager_load))

        return query


def service_factory(_context, request) -> AnnotationService:
    """Get an annotation service instance."""

    return AnnotationService(db_session=request.db)
