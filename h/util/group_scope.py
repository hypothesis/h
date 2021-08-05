from urllib.parse import SplitResult, urlsplit


def url_in_scope(url, scope_urls):
    """
    Return whether the URL match any of the scopes represented by ``scope_urls``.

    Return True if the URL matches one or more of the provided patterns (if the
    URL string begins with any of the scope URL strings)

    :arg url: URL string in question
    :arg scope_urls: List of URLs that define scopes to check against
    :type scope_urls: list(str)
    :rtype: bool
    """
    return any((url.startswith(scope_url) for scope_url in scope_urls))


def parse_scope_from_url(url):
    """
    Return a tuple representing the origin and path of a URL.

    :arg url: The URL from which to derive scope
    :type url: str
    :rtype: tuple(str, str or None)
    """
    origin = parse_origin(url)
    path = _parse_path(url) or None
    return (origin, path)


def _parse_path(url):
    """Return the path component of a URL string."""
    if url is None:
        return None
    parsed = urlsplit(url)
    return parsed.path


def parse_origin(url):
    """
    Return the origin of a URL or None if empty or invalid.

    Per https://tools.ietf.org/html/rfc6454#section-7 :
    Return ``<scheme> + '://' + <host> + <port>``
    for a URL.

    :param url: URL string
    :rtype: str or None
    """

    if url is None:
        return None

    parsed = urlsplit(url)

    if not parsed.scheme or not parsed.netloc:
        return None

    # netloc contains both host and port
    origin = SplitResult(parsed.scheme, parsed.netloc, "", "", "")
    return origin.geturl() or None
