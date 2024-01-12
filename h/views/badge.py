import re

from pyramid import httpexceptions
from sqlalchemy import text
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
    result = db.execute(text(query), {"uri": normalize(uri)}).first()
    return result[0] is True


def _regex_or(options):
    """Create a regex pattern matching any of the provided strings."""

    # An or joining non capturing groups of escaped strings
    clause = "|".join(f"(?:{re.escape(part)})" for part in options)

    if len(options) > 1:
        # Wrap the whole thing in another non-capturing group if we have
        # multiple clauses to make it easy to 'or'
        return f"(?:{clause})"

    return clause


class Blocklist:
    """Block URLs which we know are not worth replying to for the badge."""

    BLOCKED_DOMAINS = ("facebook.com", "www.facebook.com", "mail.google.com")
    BLOCKED_SCHEMES = ("chrome",)

    # This is much faster to do with a regex than URL lib. This might
    # change if the number of domains to block becomes very large. In which
    # case a Trie (like marisa-trie) might be more efficient.

    _DOMAIN_PATTERN = (
        f"(?:http[sx]?:)?//"  # An HTTP scheme (or just //)
        f"{_regex_or(BLOCKED_DOMAINS)}"  # Any of our bad domains
        "(?:/|$)"  # Followed with slash or end of string '$'
        # This part stops us from matching 'bad.com' against 'bad.com.more'
    )

    # Any of the bad schema, followed by '://'
    _SCHEME_PATTERN = f"{_regex_or(BLOCKED_SCHEMES)}://"

    # A combo pattern of the bad schemes and the bad domains
    _PATTERN = re.compile(
        # All of the '(?:)' are non capturing groups. These group things
        # together but don't remember them. This just matches either the
        # scheme pattern above or the domain pattern
        f"^(?:{_SCHEME_PATTERN})|(?:{_DOMAIN_PATTERN})",
        re.IGNORECASE,
    )

    @classmethod
    def is_blocked(cls, url):
        """Check if a URL is blocked."""

        return cls._PATTERN.match(url)


@json_view(route_name="badge")
def badge(request):
    """
    Return the number of public annotations on a given page.

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

        # Blocked things stay blocked, so we can calm down the traffic to us
        cache_control = request.response.cache_control
        cache_control.prevent_auto = True
        cache_control.public = True
        cache_control.max_age = 86400  # 1 day

        # `pyramid_authsanity` sets a response callback which adds Vary=Cookie
        # which will totally break our caching. So far there doesn't seem to be
        # much we can do about this, but browsers will still individually
        # respect the caching headers.

    elif not _has_uri_ever_been_annotated(request.db, uri):
        # Do a cheap check to see if this URI has ever been annotated. If not,
        # and most haven't, then we can skip the costs of a blocklist lookup or
        # search request. In addition to the Elasticsearch query, the search request
        # involves several DB queries to expand URIs and enumerate group IDs
        # readable by the current user.
        count = 0

    else:
        query = MultiDict({"uri": uri, "limit": 0})
        result = search.Search(request).run(query)
        count = result.total

    return {"total": count}
