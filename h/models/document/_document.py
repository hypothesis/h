import logging
from datetime import datetime
from urllib.parse import urlparse

import sqlalchemy as sa

from h.db import Base, mixins
from h.models import Annotation
from h.models.document._exceptions import ConcurrentUpdateError
from h.models.document._meta import create_or_update_document_meta
from h.models.document._uri import DocumentURI, create_or_update_document_uri
from h.util.uri import normalize as uri_normalize

log = logging.getLogger(__name__)


class Document(Base, mixins.Timestamps):
    __tablename__ = "document"

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)

    #: The denormalized value of the first DocumentMeta record with type title.
    title = sa.Column("title", sa.UnicodeText())

    #: The denormalized value of the "best" http(s) DocumentURI for this Document.
    web_uri = sa.Column("web_uri", sa.UnicodeText())

    # FIXME: This relationship should be named `uris` again after the
    #        dependency on the annotator-store is removed, as it clashes with
    #        making the Postgres and Elasticsearch interface of a Document
    #        object behave the same way.
    document_uris = sa.orm.relationship(
        "DocumentURI", backref="document", order_by="DocumentURI.updated.desc()"
    )
    meta = sa.orm.relationship(
        "DocumentMeta", backref="document", order_by="DocumentMeta.updated.desc()"
    )

    def __repr__(self):
        return f"<Document {self.id}>"

    def update_web_uri(self):
        """
        Update the value of the self.web_uri field.

        Set self.web_uri to the "best" http(s) URL from self.document_uris.
        Set self.web_uri to None if there's no http(s) DocumentURIs.
        """

        def first_http_url(type_=None):
            """
            Return this document's first http(s) URL of the given type.

            Return None if this document doesn't have any http(s) URLs of the
            given type.

            If no type is given just return this document's first http(s)
            URL, or None.
            """
            for document_uri in self.document_uris:
                uri = document_uri.uri
                if type_ is not None and document_uri.type != type_:
                    continue
                if urlparse(uri).scheme not in ["http", "https"]:
                    continue
                return document_uri.uri

        self.web_uri = (
            first_http_url(type_="self-claim")
            or first_http_url(type_="rel-canonical")
            or first_http_url()
        )

    @classmethod
    def find_by_uris(cls, session, uris):
        """Find documents by a list of uris."""
        query_uris = [uri_normalize(u) for u in uris]

        matching_claims = (
            session.query(DocumentURI)
            .filter(
                DocumentURI.uri_normalized.in_(query_uris)  # pylint: disable=no-member
            )
            .distinct(DocumentURI.document_id)
            .subquery()
        )

        return session.query(Document).join(matching_claims)

    @classmethod
    def find_or_create_by_uris(  # pylint: disable=too-many-arguments
        cls, session, claimant_uri, uris, created=None, updated=None
    ):
        """
        Find or create documents from a claimant uri and a list of uris.

        It tries to find a document based on the claimant and the set of uris.
        If none can be found it will return a new document with the claimant
        uri as its only document uri as a self-claim. It is the callers
        responsibility to create any other document uris.
        """

        finduris = [claimant_uri] + uris
        documents = cls.find_by_uris(session, finduris)

        if not documents.count():
            doc = Document(created=created, updated=updated)
            DocumentURI(
                document=doc,
                claimant=claimant_uri,
                uri=claimant_uri,
                type="self-claim",
                created=created,
                updated=updated,
            )
            session.add(doc)

        try:
            session.flush()
        except sa.exc.IntegrityError as err:
            raise ConcurrentUpdateError("concurrent document creation") from err

        return documents


def merge_documents(session, documents, updated=None):
    """
    Take a list of documents and merges them together. It returns the new master document.

    The support for setting a specific value for the `updated` should only
    be used during the Postgres migration. It should be removed afterwards.
    """

    if updated is None:
        updated = datetime.utcnow()

    master = documents[0]
    duplicates = documents[1:]
    duplicate_ids = [doc.id for doc in duplicates]

    log.info("Merging %s documents", len(duplicate_ids) + 1)

    for doc in duplicates:
        for _ in range(len(doc.document_uris)):
            uri = doc.document_uris.pop()
            uri.document = master
            uri.updated = updated

        for _ in range(len(doc.meta)):
            meta = doc.meta.pop()
            meta.document = master
            meta.updated = updated

    try:  # pylint:disable=too-many-try-statements
        session.flush()
        session.query(Annotation).filter(
            Annotation.document_id.in_(duplicate_ids)
        ).update({Annotation.document_id: master.id}, synchronize_session="fetch")
        session.query(Document).filter(Document.id.in_(duplicate_ids)).delete(
            synchronize_session="fetch"
        )
    except sa.exc.IntegrityError as err:
        raise ConcurrentUpdateError("concurrent document merges") from err

    return master


def update_document_metadata(  # pylint: disable=too-many-arguments
    session,
    target_uri,
    document_meta_dicts,
    document_uri_dicts,
    created=None,
    updated=None,
):
    """
    Create and update document metadata from the given annotation.

    Document, DocumentURI and DocumentMeta objects will be created, updated
    and deleted in the database as required by the given annotation and
    document meta and uri dicts.

    :param target_uri: the target_uri of the annotation from which the document metadata comes from
    :param document_meta_dicts: the document metadata dicts that were derived
        by validation from the "document" dict that the client posted
    :type document_meta_dicts: list of dicts

    :param document_uri_dicts: the document URI dicts that were derived by
        validation from the "document" dict that the client posted
    :type document_uri_dicts: list of dicts

    :param created: Date and time value for the new document records
    :param updated: Date and time value for the new document records

    :returns: the matched or created document
    :rtype: h.models.Document
    """
    if created is None:
        created = datetime.utcnow()
    if updated is None:
        updated = datetime.utcnow()

    documents = Document.find_or_create_by_uris(
        session,
        target_uri,
        [u["uri"] for u in document_uri_dicts],
        created=created,
        updated=updated,
    )

    if documents.count() > 1:
        document = merge_documents(session, documents, updated=updated)
    else:
        document = documents.first()

    document.updated = updated

    for document_uri_dict in document_uri_dicts:
        create_or_update_document_uri(
            session=session,
            document=document,
            created=created,
            updated=updated,
            **document_uri_dict,
        )

    document.update_web_uri()

    for document_meta_dict in document_meta_dicts:
        create_or_update_document_meta(
            session=session,
            document=document,
            created=created,
            updated=updated,
            **document_meta_dict,
        )

    return document
