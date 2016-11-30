"""
Helpers for account forms
"""

import re

from h._compat import urlparse


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
    parsed_url = urlparse.urlparse(url)

    if not parsed_url.scheme:
        parsed_url = urlparse.urlparse('http://' + url)

    if not re.match('https?', parsed_url.scheme):
        raise ValueError('Links must have an "http" or "https" prefix')

    if not parsed_url.netloc:
        raise ValueError('Links must include a domain name')

    return parsed_url.geturl()


def validate_orcid(orcid):
    """
    Validate an ORCID identifier.

    Verify that an ORCID identifier conforms to the structure described at
    http://support.orcid.org/knowledgebase/articles/116780-structure-of-the-orcid-identifier

    Returns the normalized ORCID if successfully parsed or raises a ValueError
    otherwise.
    """
    ORCID_REGEX = '\A[0-9]{4}-[0-9]{4}-[0-9]{4}-[0-9]{3}[0-9X]\Z'

    if not re.match(ORCID_REGEX, orcid):
        raise ValueError('The format of this ORCID is incorrect'.format(orcid))

    if _orcid_checksum_digit(orcid[:-1]) != orcid[-1:]:
        raise ValueError('{} is not a valid ORCID'.format(orcid))

    return True


def _orcid_checksum_digit(orcid):
    """
    Return the checksum digit for an ORCID identifier.

    Translated from the example ISO 7064 checksum implementation at
    http://support.orcid.org/knowledgebase/articles/116780-structure-of-the-orcid-identifier

    :param orcid: ORCID ID consisting of hyphens and digits, assumed to be in
                  the correct format.
    """
    total = 0
    digits = [int(ch) for ch in orcid.replace('-', '')]
    for digit in digits:
        total = (total + digit) * 2
    remainder = total % 11
    result = (12 - remainder) % 11

    if result == 10:
        return 'X'
    else:
        return str(result)
