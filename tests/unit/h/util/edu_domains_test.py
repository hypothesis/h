import pytest

from h.util.edu_domains import is_edu_email, parse_domains

# "edu" on its own matches every *.edu address. The real list has no entry that
# broad, but it is what the malformed-domain cases below have to get past.
DOMAINS = frozenset({"edu", "stanford.edu", "ox.ac.uk", "unimelb.edu.au"})


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
        ],
    )
    def test_it_matches_educational_domains(self, email):
        assert is_edu_email(email, DOMAINS) is True

    @pytest.mark.parametrize(
        "email",
        [
            "someone@gmail.com",
            # Not a subdomain of "ox.ac.uk", just a domain ending in it.
            "someone@fox.ac.uk",
            # Not a subdomain of "edu", just a domain ending in those letters.
            "someone@notedu",
            "someone@fakeedu.com",
        ],
    )
    def test_it_rejects_other_domains(self, email):
        assert is_edu_email(email, DOMAINS) is False

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
        assert is_edu_email(email, DOMAINS) is False

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
        assert is_edu_email(email, DOMAINS) is False


class TestParseDomains:
    def test_it_parses_the_list(self):
        text = "# A comment\n# Another one\ndomain\nox.ac.uk\nstanford.edu\n"

        assert parse_domains(text) == (frozenset({"ox.ac.uk", "stanford.edu"}), [])

    def test_it_accepts_crlf_line_endings(self):
        assert parse_domains("domain\r\nstanford.edu\r\n") == (
            frozenset({"stanford.edu"}),
            [],
        )

    def test_it_ignores_blank_lines(self):
        assert parse_domains("domain\n\nstanford.edu\n\n") == (
            frozenset({"stanford.edu"}),
            [],
        )

    @pytest.mark.parametrize(
        "malformed",
        # The formats these lists usually ship in, and the ones a careless edit
        # produces. None of them could ever match an address, so they are
        # reported rather than kept, and rather than quietly fixed.
        [".edu", "*.edu", "*.stanford.edu", "EDU", " stanford.edu", "stanford..edu"],
    )
    def test_it_returns_malformed_entries_apart(self, malformed):
        assert parse_domains(f"domain\nox.ac.uk\n{malformed}\n") == (
            frozenset({"ox.ac.uk"}),
            [malformed],
        )

    def test_it_returns_nothing_for_an_empty_list(self):
        assert parse_domains("# Only comments\ndomain\n") == (frozenset(), [])
