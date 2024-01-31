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

    for redirect in redirects:
        if redirect.prefix and path.startswith(redirect.src):
            suffix = path.replace(redirect.src, "", 1)
            return _dst_root(request, redirect) + suffix
        if not redirect.prefix and path == redirect.src:
            return _dst_root(request, redirect)
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
        except ValueError as err:
            raise ParseError(f"invalid redirect specification: {line!r}") from err
        if typ == "internal-exact":
            redirect = Redirect(prefix=False, internal=True, src=src, dst=dst)
        elif typ == "internal-prefix":
            redirect = Redirect(prefix=True, internal=True, src=src, dst=dst)
        elif typ == "exact":
            redirect = Redirect(prefix=False, internal=False, src=src, dst=dst)
        elif typ == "prefix":
            redirect = Redirect(prefix=True, internal=False, src=src, dst=dst)
        else:
            raise ParseError(f"unknown redirect type: {typ!r}")
        result.append(redirect)
    return result


def _dst_root(request, redirect):
    if redirect.internal:
        return request.route_url(redirect.dst)

    return redirect.dst
