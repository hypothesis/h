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


def validate_orcid(orcid):
    """
    Validate an ORCID identifier.

    Verify that an ORCID identifier conforms to the structure described at
    http://support.orcid.org/knowledgebase/articles/116780-structure-of-the-orcid-identifier

    Returns the normalized ORCID iD if successfully parsed or raises a ValueError
    otherwise.
    """
    orcid_regex = r"\A[0-9]{4}-[0-9]{4}-[0-9]{4}-[0-9]{3}[0-9X]\Z"

    if not re.match(orcid_regex, orcid):
        raise ValueError(f"The format of this ORCID iD is incorrect: {orcid}")  # noqa: EM102, TRY003

    if _orcid_checksum_digit(orcid[:-1]) != orcid[-1:]:
        raise ValueError(f"{orcid} is not a valid ORCID iD")  # noqa: EM102, TRY003

    return True


def _orcid_checksum_digit(orcid):
    """
    Return the checksum digit for an ORCID identifier.

    Translated from the example ISO 7064 checksum implementation at
    http://support.orcid.org/knowledgebase/articles/116780-structure-of-the-orcid-identifier

    :param orcid: ORCID iD consisting of hyphens and digits, assumed to be in
                  the correct format.
    """
    total = 0
    digits = [int(ch) for ch in orcid.replace("-", "")]
    for digit in digits:
        total = (total + digit) * 2
    remainder = total % 11
    result = (12 - remainder) % 11

    if result == 10:
        return "X"

    return str(result)
