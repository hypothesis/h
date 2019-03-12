# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import sqlalchemy as sa

from h._compat import urlparse
from h.db import Base
from h.util.group_scope import uri_to_scope


class GroupScope(Base):
    """
    A "scope" that limits the resources that can be annotated in a group.

    For example a group with group.scopes = ["https://example.com", "https://biopub.org"]
    is constrained to being used to annotate resources on https://example.com
    and https://biopub.org, other sites can't be annotated in this group.

    """

    __tablename__ = "groupscope"

    __table_args__ = (
        # Add a composite index of the (origin, path) columns for better
        # lookup performance.
        sa.Index("ix__groupscope__scope", "origin", "path"),
    )

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    group_id = sa.Column(
        sa.Integer, sa.ForeignKey("group.id", ondelete="cascade"), nullable=False
    )

    #: A web origin as defined by the ``origin`` property of the URL Web API:
    #: https://developer.mozilla.org/en-US/docs/Web/API/URL. This includes the
    #: scheme, domain (including subdomains) and port parts of a URL. For
    #: example:
    #:
    #: http://example.com
    #: https://web.hypothes.is
    #: http://localhost:5000
    origin = sa.Column(sa.UnicodeText, nullable=False)

    #: A path which, concatenated with ``origin``, creates a wildcarded prefix
    #: against which URLs may be compared for scope. This allows for scope
    #: granularity at a path level (instead of just origin).
    #: e.g. for a group with scope origin ``https://foo.com`` and a path ``/bar``:
    #:
    #: * ``https://foo.com/bar/baz.html`` in scope
    #: * ``https://foo.com/ding/foo.html`` NOT in scope
    path = sa.Column(sa.UnicodeText, nullable=True)

    @property
    def scope(self):
        """Return a URI composed from the origin and path attrs"""
        return urlparse.urljoin(self.origin, self.path)

    @scope.setter
    def scope(self, value):
        """Take a URI and split it into origin, path"""
        self.origin, self.path = uri_to_scope(value)

    def __repr__(self):
        return "<GroupScope %s>" % self.origin
