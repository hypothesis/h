# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import sqlalchemy as sa

from h.db import Base


class GroupScope(Base):
    """
    A "scope" that limits the resources that can be annotated in a group.

    For example a group with group.scopes = ["https://example.com", "https://biopub.org"]
    is constrained to being used to annotate resources on https://example.com
    and https://biopub.org, other sites can't be annotated in this group.

    """
    __tablename__ = 'groupscope'
    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    group_id = sa.Column(sa.Integer, sa.ForeignKey('group.id', ondelete='cascade'), nullable=False)

    #: A web origin as defined by the ``origin`` property of the URL Web API:
    #: https://developer.mozilla.org/en-US/docs/Web/API/URL. This includes the
    #: scheme, domain (including subdomains) and port parts of a URL. For
    #: example:
    #:
    #: http://example.com
    #: https://web.hypothes.is
    #: http://localhost:5000
    origin = sa.Column(sa.UnicodeText, nullable=False)

    def __repr__(self):
        return '<GroupScope %s>' % self.origin
