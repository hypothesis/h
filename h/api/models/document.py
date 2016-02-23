# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import aliased

from h.api import uri
from h.api.db import Base
from h.api.db import mixins
from h._compat import text_type


class Document(Base, mixins.Timestamps):
    __tablename__ = 'document'

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)

    uris = sa.orm.relationship('DocumentURI', backref='document')
    meta = sa.orm.relationship('DocumentMeta', backref='document')

    def __repr__(self):
        return '<Document %s>' % self.id

    @classmethod
    def find_by_uris(cls, session, uris):
        """Find documents by a list of uris."""
        query_uris = [text_type(uri.normalize(u), 'utf-8') for u in uris]

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
        self._claimant_normalized = text_type(uri.normalize(value), 'utf-8')

    @hybrid_property
    def claimant_normalized(self):
        return self._claimant_normalized

    @hybrid_property
    def uri(self):
        return self._uri

    @uri.setter
    def uri(self, value):
        self._uri = value
        self._uri_normalized = text_type(uri.normalize(value), 'utf-8')

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
        self._claimant_normalized = text_type(uri.normalize(value), 'utf-8')

    @hybrid_property
    def claimant_normalized(self):
        return self._claimant_normalized

    def __repr__(self):
        return '<DocumentMeta %s>' % self.id


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
        for _ in range(len(doc.uris)):
            u = doc.uris.pop()
            u.document = master
            u.updated = updated

        for _ in range(len(doc.meta)):
            m = doc.meta.pop()
            m.document = master
            m.updated = updated

        session.delete(doc)

    return master
