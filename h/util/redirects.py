# -*- coding: utf-8 -*-

"""
Utilities for processing a set of redirect specifications from a text file.

Redirects can be specified in a simple text-based format, in which each line
consists of three whitespace-delimited fields:

    <source path> <redirect type> <destination>

The redirect type can be one of the following:

    exact           - requests with paths that exactly match the specified
                      source path will be redirected to the destination URL.
    prefix          - requests with paths that start with the specified source
                      path will be redirected to URLs relative to the
                      destination URL.
    internal-exact  - same as `exact`, but the destination will be treated as
                      a route name rather than a URL.
    internal-prefix - same as `prefix`, but the destination will be treated as
                      a route name rather than a URL.

Lines that contain only whitespace, or which start with a '#' character, will
be ignored.
"""
from __future__ import unicode_literals

from collections import namedtuple


class Redirect(
    namedtuple(
        "Redirect",
        [
            "src",  # matching prefix (if prefix redirect) or path (if exact)
            "dst",  # route name (if internal redirect) or URL (if external)
            "prefix",  # prefix redirect if true, exact otherwise
            "internal",  # internal redirect if true, external otherwise
        ],
    )
):
    pass


class ParseError(Exception):
    pass


def lookup(redirects, request):
    """
    Check if a request matches any of a list of redirects.

    Returns None if the request does not match, and the URL to redirect to
    otherwise.
    """

    # Compute and cache `request.path` once, rather than recomputing for each
    # redirect rule that the path is matched against.
    path = request.path

    for r in redirects:
        if r.prefix and path.startswith(r.src):
            suffix = path.replace(r.src, "", 1)
            return _dst_root(request, r) + suffix
        elif not r.prefix and path == r.src:
            return _dst_root(request, r)
    return None


def parse(specs):
    """Parse a list of redirects from a sequence of redirect specifiers."""
    result = []
    for line in specs:
        # Ignore comments and blank lines
        if line.startswith("#") or not line.strip():
            continue

        try:
            src, typ, dst = line.split(None, 3)
        except ValueError:
            raise ParseError("invalid redirect specification: {!r}".format(line))
        if typ == "internal-exact":
            r = Redirect(prefix=False, internal=True, src=src, dst=dst)
        elif typ == "internal-prefix":
            r = Redirect(prefix=True, internal=True, src=src, dst=dst)
        elif typ == "exact":
            r = Redirect(prefix=False, internal=False, src=src, dst=dst)
        elif typ == "prefix":
            r = Redirect(prefix=True, internal=False, src=src, dst=dst)
        else:
            raise ParseError("unknown redirect type: {!r}".format(typ))
        result.append(r)
    return result


def _dst_root(request, redirect):
    if redirect.internal:
        return request.route_url(redirect.dst)
    else:
        return redirect.dst
