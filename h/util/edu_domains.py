"""Identify users at educational institutions from their email address."""

import re

#: One label of a hostname: alphanumerics and hyphens, and not starting or
#: ending with a hyphen, so that a label of "-" can't stand in for a real one.
#: Entries in the reference list are ASCII, so an internationalised domain only
#: matches in its punycode ("xn--") form, which this accepts.
_HOSTNAME_LABEL = re.compile(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?")


def parse_domains(text: str) -> tuple[frozenset[str], list[str]]:
    """
    Parse the reference list of educational email domains.

    The list is a one-column CSV kept in the private hypothesis/edu-domains
    repo: "#" comment lines, a "domain" header, then one domain per line.

    Entries must be bare, lower-case domains: no leading dot, no "*." wildcard,
    no surrounding whitespace. An entry matches that exact domain and any
    subdomain of it. Entries are checked rather than normalized on the way in,
    because a malformed entry would otherwise match nothing without a symptom:
    they are returned apart so that the caller can report them.

    :returns: the valid domains, and the malformed entries in file order
    """
    domains = set()
    malformed = []

    for line in text.splitlines():
        if not line or line.startswith("#") or line == "domain":
            continue

        if _is_domain(line):
            domains.add(line)
        else:
            malformed.append(line)

    return frozenset(domains), malformed


def is_edu_email(email: str | None, domains: frozenset[str]) -> bool:
    """
    Return True if `email` belongs to one of `domains`.

    A domain in the list matches itself and any of its subdomains, so the entry
    "stanford.edu" matches "someone@cs.stanford.edu" as well as
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
    if not _is_domain(domain):
        return False

    # Walk up the domain one label at a time rather than scanning the whole
    # reference list, so the cost is the depth of the domain (3 or 4 lookups)
    # rather than the size of the list.
    return any(".".join(labels[index:]) in domains for index in range(len(labels)))


def _is_domain(value: str) -> bool:
    return all(_HOSTNAME_LABEL.fullmatch(label) for label in value.split("."))
