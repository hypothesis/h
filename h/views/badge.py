# -*- coding: utf-8 -*-
# import newrelic.agent
from pyramid import httpexceptions
from webob.multidict import MultiDict

from h import search
from h.util.uri import normalize
from h.util.view import json_view


def _has_uri_ever_been_annotated(db, uri):
    """Return `True` if a given URI has ever been annotated."""

    # This check is written with SQL directly to guarantee an efficient query
    # and minimize SQLAlchemy overhead. We query `document_uri.uri_normalized`
    # instead of `annotation.target_uri_normalized` because there is an existing
    # index on `uri_normalized`.
    query = "SELECT EXISTS(SELECT 1 FROM document_uri WHERE uri_normalized = :uri)"
    result = db.execute(query, {"uri": normalize(uri)}).first()
    return result[0] is True


class Blocklist:
    """Block URLs which we know are not worth replying to for the badge."""

    BLOCKED_URL_PARTS = (
        "//facebook.com",
        "//mail.google.com",
        "//www.facebook.com",
    )

    @classmethod
    def is_blocked(cls, url):
        """Check if a URL is blocked."""

        # Dumb is fast here. I can't find a better way of doing this for now
        url = url.lower()

        for part in cls.BLOCKED_URL_PARTS:
            if part in url:
                return True

        return False


@json_view(route_name="badge")
def badge(request):
    """Return the number of public annotations on a given page.

    This is for the number that's displayed on the Chrome extension's badge.

    Certain pages are blocklisted so that the badge never shows a number on
    those pages. The Chrome extension is oblivious to this, we just tell it
    that there are 0 annotations.
    """
    # Disable NewRelic for this function.
    # newrelic.agent.ignore_transaction(flag=True)

    uri = request.params.get("uri")

    if not uri:
        raise httpexceptions.HTTPBadRequest()

    if Blocklist.is_blocked(uri):
        count = 0
    elif not _has_uri_ever_been_annotated(request.db, uri):
        # Do a cheap check to see if this URI has ever been annotated. If not,
        # and most haven't, then we can skip the costs of a blocklist lookup or
        # search request. In addition to the Elasticsearch query, the search request
        # involves several DB queries to expand URIs and enumerate group IDs
        # readable by the current user.
        count = 0
    else:
        query = MultiDict({"uri": uri, "limit": 0})
        s = search.Search(request)
        result = s.run(query)
        count = result.total

    return {"total": count}
