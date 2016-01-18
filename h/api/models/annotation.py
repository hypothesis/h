# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

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
    target_uri = sa.Column(sa.UnicodeText)
    #: The URI of the annotated page in normalized form.
    target_uri_normalized = sa.Column(sa.UnicodeText)
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

    def __repr__(self):
        return '<Annotation %s>' % self.id
