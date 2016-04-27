# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from pyramid import security
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.hybrid import hybrid_property

from h.api import uri
from h.api.db import Base
from h.api.db import mixins
from h.api.db import types


class Annotation(Base, mixins.Timestamps):

    """Model class representing a single annotation."""

    __tablename__ = 'annotation'
    __table_args__ = (
        # Tags are stored in an array-type column, and indexed using a
        # generalised inverted index. For more information on the use of GIN
        # indices for array columns, see:
        #
        #   http://www.databasesoup.com/2015/01/tag-all-things.html
        #   http://www.postgresql.org/docs/9.5/static/gin-intro.html
        #
        sa.Index('ix__annotation_tags', 'tags', postgresql_using='gin'),
        sa.Index('ix__annotation_updated', 'updated'),
    )

    #: Annotation ID: these are stored as UUIDs in the database, and mapped
    #: transparently to a URL-safe Base64-encoded string.
    id = sa.Column(types.URLSafeUUID,
                   server_default=sa.func.uuid_generate_v1mc(),
                   primary_key=True)

    #: The full userid (e.g. 'acct:foo@example.com') of the owner of this
    #: annotation.
    userid = sa.Column(sa.UnicodeText,
                       nullable=False,
                       index=True)
    #: The string id of the group in which this annotation is published.
    #: Defaults to the global public group, "__world__".
    groupid = sa.Column(sa.UnicodeText,
                        default='__world__',
                        server_default='__world__',
                        nullable=False,
                        index=True)

    #: The textual body of the annotation.
    text = sa.Column(sa.UnicodeText)
    #: The tags associated with the annotation.
    tags = sa.Column(pg.ARRAY(sa.UnicodeText, zero_indexes=True))

    #: A boolean indicating whether this annotation is shared with members of
    #: the group it is published in. "Private"/"Only me" annotations have
    #: shared=False.
    shared = sa.Column(sa.Boolean,
                       nullable=False,
                       default=False,
                       server_default=sa.sql.expression.false())

    #: The URI of the annotated page, as provided by the client.
    _target_uri = sa.Column('target_uri', sa.UnicodeText)
    #: The URI of the annotated page in normalized form.
    _target_uri_normalized = sa.Column('target_uri_normalized', sa.UnicodeText)
    #: The serialized selectors for the annotation on the annotated page.
    target_selectors = sa.Column(types.AnnotationSelectorJSONB,
                                 default=list,
                                 server_default=sa.func.jsonb('[]'))

    #: An array of annotation IDs which are ancestors of this annotation.
    references = sa.Column(pg.ARRAY(types.URLSafeUUID),
                           default=list,
                           server_default=sa.text('ARRAY[]::uuid[]'))

    #: Any additional serialisable data provided by the client.
    extra = sa.Column(pg.JSONB, nullable=True)

    document = sa.orm.relationship('Document',
                                   secondary='join(DocumentURI, Document, DocumentURI.document_id == Document.id)',
                                   primaryjoin='Annotation.target_uri_normalized == DocumentURI.uri_normalized',
                                   uselist=False)

    @hybrid_property
    def target_uri(self):
        return self._target_uri

    @target_uri.setter
    def target_uri(self, value):
        self._target_uri = value
        self._target_uri_normalized = uri.normalize(value)

    @hybrid_property
    def target_uri_normalized(self):
        return self._target_uri_normalized

    @property
    def parent_id(self):
        """
        Return the ID of the annotation that this annotation is a reply to.

        Return None if this annotation is not a reply.

        """
        if self.references:
            return self.references[-1]

    def __acl__(self):
        """Return a Pyramid ACL for this annotation."""
        acl = []
        if self.shared:
            group = 'group:{}'.format(self.groupid)
            if self.groupid == '__world__':
                group = security.Everyone

            acl.append((security.Allow, group, 'read'))
        else:
            acl.append((security.Allow, self.userid, 'read'))

        for action in ['admin', 'update', 'delete']:
            acl.append((security.Allow, self.userid, action))

        # If we haven't explicitly authorized it, it's not allowed.
        acl.append(security.DENY_ALL)

        return acl

    def __repr__(self):
        return '<Annotation %s>' % self.id
