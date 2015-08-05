# -*- coding: utf-8 -*-

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
   speaking? (AKA "normalisation".)

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

This package is responsible for defining URI normalisation and expansion
routines for use elsewhere in the Hypothesis application.
"""

import urllib
import urlparse

from h.api import models


URL_SCHEMES = set(['http', 'https'])

BLACKLISTED_QUERY_PARAMS = set([
    # Google Analytics campaigns. Reference:
    #
    #     https://support.google.com/analytics/answer/1033867?hl=en
    #
    'utm_campaign',
    'utm_content',
    'utm_medium',
    'utm_source',
    'utm_term',
])

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


def normalise(uristr):
    """Translate the given URI into a normalised form."""
    uristr = uristr.encode('utf-8')

    # Try to extract the scheme
    uri = urlparse.urlsplit(uristr)

    # If this isn't a URL, we don't perform any normalisation
    if uri.scheme.lower() not in URL_SCHEMES:
        return uristr

    scheme = uri.scheme
    netloc = _normalise_netloc(uri)
    path = _normalise_path(uri)
    query = _normalise_query(uri)
    fragment = None

    uri = urlparse.SplitResult(scheme, netloc, path, query, fragment)

    return uri.geturl()


def expand(uri):
    """
    Return all URIs which refer to the same underlying document as `uri`.

    This function determines whether we already have "document" records for the
    passed URI, and if so returns the set of all URIs which we currently
    believe refer to the same document.
    """
    doc = models.Document.get_by_uri(uri)
    if doc is None:
        return [uri]
    return doc.uris()


def _normalise_netloc(uri):
    netloc = uri.netloc
    ipv6_hostname = '[' in netloc and ']' in netloc

    username = uri.username
    password = uri.password
    hostname = uri.hostname
    port = uri.port

    # Normalise hostname to lower case
    hostname = hostname.lower()

    # Remove port if default for the scheme
    if uri.scheme == 'http' and port == 80:
        port = None
    elif uri.scheme == 'https' and port == 443:
        port = None

    # Put it all back together again...
    userinfo = None
    if username is not None:
        userinfo = username
    if password is not None:
        userinfo += ':' + password

    if ipv6_hostname:
        hostname = '[' + hostname + ']'

    hostinfo = hostname
    if port is not None:
        hostinfo += ':' + str(port)

    if userinfo is not None:
        netloc = '@'.join([userinfo, hostinfo])
    else:
        netloc = hostinfo

    return netloc


def _normalise_path(uri):
    path = uri.path

    if path.endswith('/'):
        path = path[:-1]

    segments = path.split('/')
    segments = [_normalise_pathsegment(s) for s in segments]
    path = '/'.join(segments)

    return path


def _normalise_pathsegment(segment):
    return urllib.quote(urllib.unquote(segment), safe=UNRESERVED_PATHSEGMENT)


def _normalise_query(uri):
    query = uri.query

    try:
        items = urlparse.parse_qsl(query, keep_blank_values=True)
    except ValueError:
        # If we can't parse the query string, we better preserve it as it was.
        return query

    # Python sorts are stable, so preserving relative ordering of items with
    # the same key doesn't require any work from us
    items = sorted(items, key=lambda x: x[0])

    # Remove query params that are blacklisted
    items = [i for i in items if i[0] not in BLACKLISTED_QUERY_PARAMS]

    # Normalise percent-encoding for query items
    query = _normalise_queryitems(items)

    return query


def _normalise_queryitems(items):
    segments = ['='.join([_normalise_queryname(i[0]),
                          _normalise_queryvalue(i[1])]) for i in items]
    return '&'.join(segments)


def _normalise_queryname(name):
    return urllib.quote_plus(urllib.unquote_plus(name),
                             safe=UNRESERVED_QUERY_NAME)


def _normalise_queryvalue(value):
    return urllib.quote_plus(urllib.unquote_plus(value),
                             safe=UNRESERVED_QUERY_VALUE)
