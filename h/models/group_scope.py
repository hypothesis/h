from urllib.parse import urljoin

import sqlalchemy as sa
from sqlalchemy.ext.hybrid import hybrid_property

from h.db import Base
from h.util.group_scope import parse_scope_from_url


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
    _origin = sa.Column("origin", sa.UnicodeText, nullable=False)

    @hybrid_property
    def origin(self):
        return self._origin

    #: A path which, concatenated with ``origin``, creates a wildcarded prefix
    #: against which URLs may be compared for scope. This allows for scope
    #: granularity at a path level (instead of just origin).
    #: e.g. for a group with scope origin ``https://foo.com`` and a path ``/bar``:
    #:
    #: * ``https://foo.com/bar/baz.html`` in scope
    #: * ``https://foo.com/ding/foo.html`` NOT in scope
    _path = sa.Column("path", sa.UnicodeText, nullable=True)

    @property
    def scope(self):
        """Return a URL composed from the origin and path attrs."""
        return urljoin(self._origin, self._path)

    @scope.setter
    def scope(self, value):
        """
        Take a URL and split it into origin and path.

        :raises ValueError: if URL is invalid (origin cannot be parsed)
        """
        parsed_origin, parsed_path = parse_scope_from_url(value)
        if parsed_origin is None:
            raise ValueError("Invalid URL for scope: missing origin component")
        self._origin = parsed_origin
        self._path = parsed_path

    def __repr__(self):
        return f"<GroupScope {self.scope}>"
