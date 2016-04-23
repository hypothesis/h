# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from datetime import datetime
import logging

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy.ext.hybrid import hybrid_property

from h.api.db import Base
from h.api.db import mixins
from h.api.uri import normalize as uri_normalize


log = logging.getLogger(__name__)


class Document(Base, mixins.Timestamps):
    __tablename__ = 'document'

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)

    # FIXME: This relationship should be named `uris` again after the
    #        dependency on the annotator-store is removed, as it clashes with
    #        making the Postgres and Elasticsearch interface of a Document
    #        object behave the same way.
    document_uris = sa.orm.relationship('DocumentURI', backref='document')
    meta = sa.orm.relationship('DocumentMeta', backref='document')

    def __repr__(self):
        return '<Document %s>' % self.id

    @property
    def title(self):
        titles = [m.value for m in self.meta if m.type == 'title']
        try:
            return titles[0][0]
        except IndexError:
            return None

    @classmethod
    def find_by_uris(cls, session, uris):
        """Find documents by a list of uris."""
        query_uris = [uri_normalize(u) for u in uris]

        matching_claims = (
            session.query(DocumentURI)
                   .filter(DocumentURI.uri_normalized.in_(query_uris))
                   .distinct(DocumentURI.document_id)
                   .subquery()
        )

        return session.query(Document).join(matching_claims)

    @classmethod
    def find_or_create_by_uris(cls, session, claimant_uri, uris,
                               created=None, updated=None):
        """
        Find or create documents from a claimant uri and a list of uris.

        It tries to find a document based on the claimant and the set of uris.
        If none can be found it will return a new document with the claimant
        uri as its only document uri as a self-claim. It is the callers
        responsibility to create any other document uris.
        """

        finduris = [claimant_uri] + uris
        documents = cls.find_by_uris(session, finduris)

        if documents.count() == 0:
            doc = Document(created=created, updated=updated)
            DocumentURI(document=doc,
                        claimant=claimant_uri,
                        uri=claimant_uri,
                        type='self-claim',
                        created=created,
                        updated=updated)
            session.add(doc)

        return documents


class DocumentURI(Base, mixins.Timestamps):
    __tablename__ = 'document_uri'
    __table_args__ = (
        sa.UniqueConstraint('claimant_normalized',
                            'uri_normalized',
                            'type',
                            'content_type'),
    )

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)

    _claimant = sa.Column('claimant',
                          sa.UnicodeText,
                          nullable=False)
    _claimant_normalized = sa.Column('claimant_normalized',
                                     sa.UnicodeText,
                                     nullable=False)

    _uri = sa.Column('uri',
                     sa.UnicodeText,
                     nullable=False)
    _uri_normalized = sa.Column('uri_normalized',
                                sa.UnicodeText,
                                nullable=False,
                                index=True)

    type = sa.Column(sa.UnicodeText)
    content_type = sa.Column(sa.UnicodeText)

    document_id = sa.Column(sa.Integer,
                            sa.ForeignKey('document.id'),
                            nullable=False)

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
        return '<DocumentURI %s>' % self.id


class DocumentMeta(Base, mixins.Timestamps):
    __tablename__ = 'document_meta'
    __table_args__ = (
        sa.UniqueConstraint('claimant_normalized', 'type'),
    )

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)

    _claimant = sa.Column('claimant',
                          sa.UnicodeText,
                          nullable=False)
    _claimant_normalized = sa.Column('claimant_normalized',
                                     sa.UnicodeText,
                                     nullable=False)

    type = sa.Column(sa.UnicodeText, nullable=False)
    value = sa.Column(pg.ARRAY(sa.UnicodeText, zero_indexes=True),
                      nullable=False)

    document_id = sa.Column(sa.Integer,
                            sa.ForeignKey('document.id'),
                            nullable=False)

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

    def __repr__(self):
        return '<DocumentMeta %s>' % self.id


def create_or_update_document_uri(session,
                                  claimant,
                                  uri,
                                  type,
                                  content_type,
                                  document,
                                  created,
                                  updated):
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
    :type session: sqlalchemy.orm.session.Session

    :param claimant: the .claimant property of the DocumentURI
    :type claimant: unicode

    :param uri: the .uri property of the DocumentURI
    :type uri: unicode

    :param type: the .type property of the DocumentURI
    :type type: unicode

    :param content_type: the .content_type property of the DocumentURI
    :type content_type: unicode

    :param document: the Document that the new DocumentURI will belong to, if a
        new DocumentURI is created
    :type document: h.api.models.Document

    :param created: the time that will be used as the .created time for the new
        DocumentURI, if a new one is created
    :type created: datetime.datetime

    :param updated: the time that will be set as the .updated time for the new
        or existing DocumentURI
    :type updated: datetime.datetime

    """
    docuri = session.query(DocumentURI).filter(
        DocumentURI.claimant_normalized == uri_normalize(claimant),
        DocumentURI.uri_normalized == uri_normalize(uri),
        DocumentURI.type == type,
        DocumentURI.content_type == content_type).first()

    if docuri is None:
        docuri = DocumentURI(claimant=claimant,
                             uri=uri,
                             type=type,
                             content_type=content_type,
                             document=document,
                             created=created,
                             updated=updated)
        session.add(docuri)
    elif not docuri.document == document:
        log.warn("Found DocumentURI (id: %d)'s document_id (%d) doesn't match "
                 "given Document's id (%d)",
                 docuri.id, docuri.document_id, document.id)

    docuri.updated = updated


def create_or_update_document_meta(session,
                                   claimant,
                                   type,
                                   value,
                                   document,
                                   created,
                                   updated):
    """
    Create or update a DocumentMeta with the given parameters.

    If an equivalent DocumentMeta already exists in the database then its value
    and updated time will be updated.

    If no equivalent DocumentMeta exists in the database then a new one will be
    created and added to the database.

    To be considered "equivalent" an existing DocumentMeta must have the given
    claimant and type, but its value, document and created and updated times
    needn't match the given ones.

    :param session: the database session
    :type session: sqlalchemy.orm.session.Session

    :param claimant: the value to use for the DocumentMeta's claimant attribute
        if a new DocumentMeta is created
    :type claimant: unicode

    :param type: the value of the new or existing DocumentMeta's type attribute
    :type type: unicode

    :param value: the value to set the new or existing DocumentMeta's value
        attribute to
    :type value: list of unicode strings

    :param document: the value to use for the DocumentMeta's document if a new
        DocumentMeta is created
    :type document: h.api.models.Document

    :param created: the value to use for the DocumentMeta's created attribute
        if a new DocumentMeta is created
    :type created: datetime.datetime

    :param updated: the value to set the new or existing DocumentMeta's updated
        attribute to
    :type updated: datetime.datetime

    """
    existing_dm = session.query(DocumentMeta).filter(
        DocumentMeta.claimant_normalized == uri_normalize(claimant),
        DocumentMeta.type == type).one_or_none()

    if existing_dm is None:
        session.add(DocumentMeta(
                    claimant=claimant,
                    type=type,
                    value=value,
                    document=document,
                    created=created,
                    updated=updated,
                    ))
    else:
        existing_dm.value = value
        existing_dm.updated = updated
        if not existing_dm.document == document:
            log.warn("Found DocumentMeta (id: %d)'s document_id (%d) doesn't "
                     "match given Document's id (%d)",
                     existing_dm.id, existing_dm.document_id, document.id)


def merge_documents(session, documents, updated=datetime.now()):
    """
    Takes a list of documents and merges them together. It returns the new
    master document.

    The support for setting a specific value for the `updated` should only
    be used during the Postgres migration. It should be removed afterwards.
    """
    master = documents[0]
    duplicates = documents[1:]

    for doc in duplicates:
        for _ in range(len(doc.document_uris)):
            u = doc.document_uris.pop()
            u.document = master
            u.updated = updated

        for _ in range(len(doc.meta)):
            m = doc.meta.pop()
            m.document = master
            m.updated = updated

        session.delete(doc)

    return master
