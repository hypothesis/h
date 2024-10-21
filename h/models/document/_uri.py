import logging

import sqlalchemy as sa
from sqlalchemy.ext.hybrid import hybrid_property

from h.db import Base, mixins
from h.models.document._exceptions import ConcurrentUpdateError
from h.util.uri import normalize as uri_normalize

log = logging.getLogger(__name__)


class DocumentURI(Base, mixins.Timestamps):
    __tablename__ = "document_uri"

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)

    _claimant = sa.Column("claimant", sa.UnicodeText, nullable=False)
    _claimant_normalized = sa.Column(
        "claimant_normalized", sa.UnicodeText, nullable=False
    )

    _uri = sa.Column("uri", sa.UnicodeText, nullable=False)
    _uri_normalized = sa.Column(
        "uri_normalized", sa.UnicodeText, nullable=False, index=True
    )

    type = sa.Column(sa.UnicodeText, nullable=False, default="", server_default="")
    content_type = sa.Column(
        sa.UnicodeText, nullable=False, default="", server_default=""
    )

    document_id = sa.Column(sa.Integer, sa.ForeignKey("document.id"), nullable=False)

    __table_args__ = (
        sa.Index(
            "ix__document_uri_unique",
            sa.func.md5(_claimant_normalized),
            sa.func.md5(_uri_normalized),
            "type",
            "content_type",
            unique=True,
        ),
        sa.Index("ix__document_uri_document_id", "document_id"),
        sa.Index("ix__document_uri_updated", "updated"),
    )

    @hybrid_property
    def claimant(self):
        return self._claimant

    @claimant.setter
    def claimant(self, value):
        self._claimant = value
        self._claimant_normalized = uri_normalize(value)

    @hybrid_property
    def claimant_normalized(self):
        return self._claimant_normalized

    @hybrid_property
    def uri(self):
        return self._uri

    @uri.setter
    def uri(self, value):
        self._uri = value
        self._uri_normalized = uri_normalize(value)

    @hybrid_property
    def uri_normalized(self):
        return self._uri_normalized

    def __repr__(self):
        return f"<DocumentURI {self.id}>"


def create_or_update_document_uri(  # pylint: disable=redefined-builtin,too-many-arguments, too-many-positional-arguments
    session, claimant, uri, type, content_type, document, created, updated
):
    """
    Create or update a DocumentURI with the given parameters.

    If an equivalent DocumentURI already exists in the database then its
    updated time will be updated.

    If no equivalent DocumentURI exists in the database then a new one will be
    created and added to the database.

    To be considered "equivalent" an existing DocumentURI must have the same
    claimant, uri, type and content_type, but the Document object that it
    belongs to may be different. The claimant and uri are normalized before
    comparing.

    :param session: the database session
    :param claimant: the .claimant property of the DocumentURI
    :param uri: the .uri property of the DocumentURI
    :param type: the .type property of the DocumentURI
    :param content_type: the .content_type property of the DocumentURI

    :param document: the Document that the new DocumentURI will belong to, if a
        new DocumentURI is created
    :type document: h.models.Document

    :param created: the time that will be used as the .created time for the new
        DocumentURI, if a new one is created
    :param updated: the time that will be set as the .updated time for the new
        or existing DocumentURI
    """
    docuri = (
        session.query(DocumentURI)
        .filter(
            DocumentURI.claimant_normalized == uri_normalize(claimant),
            DocumentURI.uri_normalized == uri_normalize(uri),
            DocumentURI.type == type,
            DocumentURI.content_type == content_type,
        )
        .first()
    )

    if docuri is None:
        docuri = DocumentURI(
            claimant=claimant,
            uri=uri,
            type=type,
            content_type=content_type,
            document=document,
            created=created,
            updated=updated,
        )
        session.add(docuri)
    elif not docuri.document == document:
        log.warning(
            "Found DocumentURI (id: %s)'s document_id (%s) doesn't match "
            "given Document's id (%s)",
            docuri.id,
            docuri.document_id,
            document.id,
        )

    docuri.updated = updated

    try:
        session.flush()
    except sa.exc.IntegrityError as err:
        raise ConcurrentUpdateError("concurrent document uri updates") from err
