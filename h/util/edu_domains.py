"""Identify users at educational institutions from their email address."""

import re

#: One label of a hostname: alphanumerics and hyphens, and not starting or
#: ending with a hyphen, so that a label of "-" can't stand in for a real one.
#: Entries in the reference list are ASCII, so an internationalised domain only
#: matches in its punycode ("xn--") form, which this accepts.
_HOSTNAME_LABEL = re.compile(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?")

#: Reference list of educational email domains.
#:
#: PLACEHOLDER. The real list is owned by product (see the "Collect EDU user
#: role information in the web app" PRD). Until it lands this holds only the
#: handful of entries needed to develop and test against, and "edu" on its own
#: matches every *.edu address there is. Do not enable the `instructor_survey`
#: feature flag for real users while this is still the placeholder: that flag
#: is what keeps this list from reaching them.
#:
#: Entries are bare, lower-case domains: no leading dot, no "*." wildcard, no
#: surrounding whitespace. An entry matches that exact domain and any subdomain
#: of it, so a single "edu" covers every *.edu address. The format is enforced
#: by a test rather than normalized on the way in, because a malformed entry
#: matches nothing: it would switch the survey off for everyone, silently, and
#: the most likely moment for that to happen is when the real list replaces
#: this one.
#:
#: It lives here rather than in the database because the PRD says the list is
#: static and rarely changes, and `is_edu_email` runs while building the user
#: profile, which the client requests on every launch.
EDU_DOMAINS = frozenset(
    {
        "edu",
        "ac.uk",
        "edu.au",
        # Not an educational domain: our own, so that staff accounts see the
        # survey while we test it. Goes when the real list lands.
        "hypothes.is",
    }
)


def is_edu_email(email: str | None) -> bool:
    """
    Return True if `email` belongs to a known educational institution.

    A domain in the reference list matches itself and any of its subdomains, so
    the entry "edu" matches "someone@cs.stanford.edu" as well as
    "someone@stanford.edu".
    """
    if not email:
        return False

    _, separator, domain = email.rpartition("@")
    if not separator or not domain:
        return False

    domain = domain.strip().lower()
    labels = domain.split(".")

    # Every label has to be a real hostname label before we walk the domain.
    # The failure mode this closes is junk sitting between something arbitrary
    # and a clean suffix from the list: "evil.com/.edu", "evil.com .edu" and
    # "foo..edu" all end in a label that is exactly "edu", so the walk below
    # matches them without any of them being a subdomain of anything. Checking
    # the shape of a label rules out that whole class at once; rejecting the
    # bad characters one by one does not, which is how an earlier version of
    # this guard let "evil.com/.edu" through while stopping "evil.com .edu".
    #
    # A trailing-dot FQDN ("stanford.edu.") ends in an empty label and is
    # rejected too, which is the safe direction to be wrong in.
    if not all(_HOSTNAME_LABEL.fullmatch(label) for label in labels):
        return False

    # Walk up the domain one label at a time rather than scanning the whole
    # reference list, so the cost is the depth of the domain (3 or 4 lookups)
    # rather than the size of the list.
    return any(".".join(labels[index:]) in EDU_DOMAINS for index in range(len(labels)))
