"""Helpers for account forms."""

import re
from urllib.parse import urlparse


def validate_url(url):
    """
    Validate an HTTP(S) URL as a link for a user's profile.

    Helper for use with Colander that validates a URL provided by a user as a
    link for their profile.

    Returns the normalized URL if successfully parsed or raises a ValueError
    otherwise.
    """

    # Minimal URL validation with urlparse. This is extremely lenient, we might
    # want to use something like https://github.com/kvesteri/validators instead.
    parsed_url = urlparse(url)

    if not parsed_url.scheme:
        parsed_url = urlparse("http://" + url)

    if not re.match("https?", parsed_url.scheme):
        raise ValueError('Links must have an "http" or "https" prefix')  # noqa: EM101, TRY003

    if not parsed_url.netloc:
        raise ValueError("Links must include a domain name")  # noqa: EM101, TRY003

    return parsed_url.geturl()
