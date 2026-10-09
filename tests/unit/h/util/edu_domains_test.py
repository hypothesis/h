import pytest

from h.util import edu_domains
from h.util.edu_domains import EDU_DOMAINS, is_edu_email


class TestIsEduEmail:
    @pytest.mark.parametrize(
        "email",
        [
            "someone@stanford.edu",
            # A domain in the list matches its subdomains too, which is how
            # universities usually hand out addresses.
            "someone@cs.stanford.edu",
            "someone@ox.ac.uk",
            "someone@unimelb.edu.au",
            # The reference list is lower case; addresses in the wild are not.
            "SOMEONE@Stanford.EDU",
            # Our own domain is in the placeholder list so that staff accounts
            # see the survey while we test it. This case goes with it.
            "someone@hypothes.is",
        ],
    )
    def test_it_matches_educational_domains(self, email):
        assert is_edu_email(email) is True

    @pytest.mark.parametrize(
        "email",
        [
            "someone@gmail.com",
            # Not a subdomain of "edu", just a domain ending in those letters.
            "someone@notedu",
            "someone@fakeedu.com",
        ],
    )
    def test_it_rejects_other_domains(self, email):
        assert is_edu_email(email) is False

    @pytest.mark.parametrize(
        "email",
        [
            # Every one of these ends up producing a bare "edu" label, which
            # would match the reference list without being a subdomain of
            # anything. None of them is a valid address, but is_edu_email is a
            # public helper and shouldn't rely on its caller having validated.
            "someone@evil.com .edu",
            "someone@ev il.edu",
            "someone@foo..edu",
            "someone@.edu",
            # Not whitespace, same trick. These are what a guard that only
            # rejected spaces and empty labels used to let through.
            "someone@evil.com/.edu",
            "someone@evil.com!.edu",
            "someone@evil.com_.edu",
            "someone@evil.com\x00.edu",
            "someone@-.edu",
            # Trailing-dot FQDN: rejected by the same rule, on purpose.
            "someone@stanford.edu.",
        ],
    )
    def test_it_rejects_malformed_domains(self, email):
        assert is_edu_email(email) is False

    @pytest.mark.parametrize(
        "email",
        [
            # User.email is nullable, so this has to be handled.
            None,
            "",
            "no-at-sign",
            "trailing-at@",
        ],
    )
    def test_it_rejects_unusable_values(self, email):
        assert is_edu_email(email) is False


class TestEduDomains:
    """
    Guard the format of the reference list.

    A malformed entry does not raise: it just never matches, which turns the
    survey off for everyone with no visible symptom. The two formats these
    lists usually ship in, ".edu" and "*.stanford.edu", both fail that way, so
    the most likely moment to introduce one is when the real list replaces the
    placeholder.
    """

    def test_it_is_not_empty(self):
        assert EDU_DOMAINS

    def test_entries_are_bare_lower_case_domains(self):
        # Checked against `_HOSTNAME_LABEL`, which is what `is_edu_email`
        # matches with, so the list is held to the same definition of a valid
        # domain as the addresses it's compared against -- rather than to a
        # second, looser one that would pass entries like "edu;", "-edu" or
        # "stanford..edu" while `is_edu_email` can never match them. ".edu",
        # "*.edu", "EDU" and " edu" fail it too.
        #
        # Not parametrized over the list on purpose: that is 3 pytest cases
        # with the placeholder and 14k once the real list lands.
        malformed = sorted(
            domain
            for domain in EDU_DOMAINS
            if not all(
                edu_domains._HOSTNAME_LABEL.fullmatch(label)  # noqa: SLF001
                for label in domain.split(".")
            )
        )

        assert not malformed, f"malformed entries: {malformed}"

    @pytest.mark.parametrize("malformed", [".edu", "*.edu", "*.stanford.edu", "EDU"])
    def test_a_malformed_entry_would_match_nothing(self, malformed, monkeypatch):
        # Demonstrates why the test above exists rather than normalizing the
        # entries quietly: none of these raise, they just stop matching.
        monkeypatch.setattr(edu_domains, "EDU_DOMAINS", frozenset({malformed}))

        assert is_edu_email("someone@stanford.edu") is False
