"""
Tools for dealing with URIs within the Hypothesis API.

There are two main ways of considering the relationship between annotations and
annotated objects:

1. Annotations are, practically speaking, made on web pages, and thus they have
   a URL associated with them.

2. Annotations are made on documents, and the particular HTML or PDF page being
   annotated is merely a specific manifestation of the abstract document that
   is being annotated. In this scenario, a document may be identified by one or
   more URIs.

The second model is more complex from both a conceptual point of view and in
terms of implementation, but it offers substantial benefits. If we talk of
annotations attached to documents, without regard to presentation format or
location, we are able to do many interesting things:

- Alice makes an annotation on a PDF; Bob visits an HTML version of the same
  document, and sees Alice's annotation.
- Alice makes an annotation on an Instapaper-hosted version of a web page which
  contains a <link rel=canonical> tag. Bob visits the original article and sees
  Alice's annotation.
- Bob makes an annotation on a PDF which is on his local machine. Alice opens
  the same PDF on her machine, and see's Bob's annotations even if the PDF has
  never been uploaded to a webserver. (We can do this because of the
  immutability of PDF documents -- we can uniquely fingerprint each one and
  form a "URN" of the form "urn:x-pdf:<fingerprint>".)

The challenge, then, is to enable these features without making the public API
for creating and updating annotations overly complex. It turns out this is
possible if we can answer two questions:

1. Given two URI strings, do they both refer to the same URI, practically
   speaking? (AKA "normalization".)

   e.g. on the web, the following URLs will *usually* refer to the same web
   page::

       http://example.com/foo?a=hello&b=world
       http://exAMPle.com/foo?a=hello&b=world
       http://example.com/foo/?a=hello&b=world
       http://example.com/foo?b=world&a=hello
       http://example.com/foo?a=hello&b=world#somefragment

2. Given a URI, what are all the known URIs of the underlying *document* (in
   the sense given above). (AKA "expansion".)

   e.g. we may know (from page metadata or otherwise) that all the following
   URIs refer to the same content, even if in differing formats::

       http://example.com/research/papers/2015-discoveries.html
       http://example.com/research/papers/2015-discoveries.pdf
       http://example.org/reprints/example-com-2015-discoveries.pdf
       urn:x-pdf:c83fa94bd1d522276a32f81682a43d29
       urn:doi:10.1000/12345

This package is responsible for defining URI normalization routines for use
elsewhere in the Hypothesis application. URI expansion is handled by
:py:func:`h.storage.expand_uri`.
"""

import re
from urllib.parse import (
    SplitResult,
    parse_qsl,
    quote,
    quote_plus,
    unquote,
    unquote_plus,
    urlparse,
    urlsplit,
)

URL_SCHEMES = {"http", "https"}

# List of regular expressions matching the names of query parameters that we
# strip from URLs as part of normalization.
BLACKLISTED_QUERY_PARAMS = [
    re.compile(regex)
    for regex in (
        # Google AdWords tracking identifier. Reference:
        #
        #    https://support.google.com/analytics/answer/2938246?hl=en
        #
        r"^gclid$",
        # Google Analytics campaigns. Reference:
        #
        #    https://support.google.com/analytics/answer/1033867?hl=en
        #
        r"^utm_(campaign|content|medium|source|term)$",
        # WebTrends Analytics query params. Reference:
        #
        #    http://help.webtrends.com/en/analytics10/#qpr_about.html
        #
        r"^WT\..+$",
        # Amazon security access token. Reference:
        #
        #    https://docs.aws.amazon.com/general/latest/gr/sigv4-add-signature-to-request.html
        #
        r"(?i)^x-amz-security-token$",
        #
        # Google Drive resource key. Reference:
        #
        #    https://support.google.com/a/answer/10685032
        r"^resourcekey$",
    )
]

# From RFC3986. The ABNF for path segments is
#
#   path-abempty  = *( "/" segment )
#   ...
#   segment       = *pchar
#   ...
#   pchar         = unreserved / pct-encoded / sub-delims / ":" / "@"
#   ...
#   unreserved    = ALPHA / DIGIT / "-" / "." / "_" / "~"
#   sub-delims    = "!" / "$" / "&" / "'" / "(" / ")"
#                    / "*" / "+" / "," / ";" / "="
#
# Taken together, this implies the following set of "unreserved" characters for
# path segments (excluding ALPHA and DIGIT which are handled already).
UNRESERVED_PATHSEGMENT = "-._~:@!$&'()*+,;="

# From RFC3986. The ABNF for query strings is
#
#   query         = *( pchar / "/" / "?" )
#
# Where the definition of pchar is as given above.
#
# We exclude "&" and ";" from both names and values, and "=" from names, as
# they are used as delimiters in HTTP URL query strings. In addition, "+" is
# used to denote the space character, so for legacy reasons this is also
# excluded.
UNRESERVED_QUERY_NAME = "-._~:@!$'()*,"
UNRESERVED_QUERY_VALUE = "-._~:@!$'()*,="

# The string that gets prefixed onto a URI if you paste the URI into our Via
# form. For example pasting https://example.com would
# redirect your browser to https://via.hypothes.is/https://example.com.
VIA_PREFIX = "https://via.hypothes.is/"


def normalize(uristr):
    """
    Translate the given URI into a normalized form.

    :type uristr: unicode
    :rtype: unicode
    """

    # Strip proxy prefix for proxied URLs
    for scheme in URL_SCHEMES:
        if uristr.startswith(VIA_PREFIX + scheme + ":"):
            uristr = uristr[len(VIA_PREFIX) :]
            break

    # Try to extract the scheme
    uri = urlsplit(uristr)

    # If this isn't a URL, we don't perform any normalization
    if uri.scheme.lower() not in URL_SCHEMES:
        return uristr

    # Don't perform normalization on URLs with no hostname.
    if uri.hostname is None:
        return uristr

    scheme = _normalize_scheme(uri)
    netloc = _normalize_netloc(uri)
    path = _normalize_path(uri)
    query = _normalize_query(uri)
    fragment = None

    uri = SplitResult(scheme, netloc, path, query, fragment)

    return uri.geturl()


def origin(url):
    """
    Return a copy of ``url`` with the path, query string and fragment removed.

    ``url`` is assumed to be an HTTP(S) URL.
    """
    url_parts = urlsplit(url)
    return SplitResult(url_parts.scheme, url_parts.netloc, "", "", "").geturl()


def _normalize_scheme(uri):
    scheme = uri.scheme

    if scheme in URL_SCHEMES:  # pragma: no cover
        scheme = "httpx"

    return scheme


def _normalize_netloc(uri):
    netloc = uri.netloc
    ipv6_hostname = "[" in netloc and "]" in netloc

    username = uri.username
    password = uri.password
    hostname = uri.hostname
    port = uri.port

    # Normalise hostname to lower case
    hostname = hostname.lower()

    # Remove port if default for the scheme
    if uri.scheme == "http" and port == 80:
        port = None
    elif uri.scheme == "https" and port == 443:
        port = None

    # Put it all back together again...
    userinfo = None
    if username is not None:
        userinfo = username
    if password is not None:
        userinfo += ":" + password

    if ipv6_hostname:
        hostname = "[" + hostname + "]"

    hostinfo = hostname
    if port is not None:
        hostinfo += ":" + str(port)

    if userinfo is not None:
        netloc = "@".join([userinfo, hostinfo])
    else:
        netloc = hostinfo

    return netloc


def _normalize_path(uri):
    path = uri.path

    while path.endswith("/"):
        path = path[:-1]

    segments = path.split("/")
    segments = [_normalize_pathsegment(s) for s in segments]
    path = "/".join(segments)

    return path


def _normalize_pathsegment(segment):
    return quote(unquote(segment), safe=UNRESERVED_PATHSEGMENT)


def _normalize_query(uri):
    query = uri.query

    try:
        items = parse_qsl(query, keep_blank_values=True, strict_parsing=True)
    except ValueError:
        # If we can't parse the query string, we better preserve it as it was.
        return query

    # Python sorts are stable, so preserving relative ordering of items with
    # the same key doesn't require any work from us
    items = sorted(items, key=lambda x: x[0])

    # Remove query params that are blacklisted
    items = [i for i in items if not _blacklisted_query_param(i[0])]

    # Normalise percent-encoding for query items
    query = _normalize_queryitems(items)

    return query


def _normalize_queryitems(items):
    segments = [
        "=".join([_normalize_queryname(i[0]), _normalize_queryvalue(i[1])])
        for i in items
    ]
    return "&".join(segments)


def _normalize_queryname(name):
    return quote_plus(unquote_plus(name), safe=UNRESERVED_QUERY_NAME)


def _normalize_queryvalue(value):
    return quote_plus(unquote_plus(value), safe=UNRESERVED_QUERY_VALUE)


def _blacklisted_query_param(string):
    """Return True if the given string matches any BLACKLISTED_QUERY_PARAMS."""
    return any(patt.match(string) for patt in BLACKLISTED_QUERY_PARAMS)


def render_url_template(template, example_url):
    """
    Update a URL template to have the same scheme and host as the example.

    This function is primarily used in development to support creating
    absolute links to h or other Hypothesis services which work when h is
    accessed from the same system (where the h dev server is "localhost:<port>")
    or a different device (when the h dev server is "machine-name.local:<port>").
    """
    parsed = urlparse(example_url)

    url = template.replace("{current_host}", parsed.hostname)
    url = url.replace("{current_scheme}", parsed.scheme)
    return url
