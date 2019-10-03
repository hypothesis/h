import pytest

from h.accounts.util import validate_orcid, validate_url


def test_validate_url_rejects_urls_without_domains():
    with pytest.raises(ValueError):
        validate_url("http:///path")


def test_validate_url_adds_http_prefix():
    assert validate_url("github.com/jimsmith") == "http://github.com/jimsmith"


def test_validate_url_accepts_http_urls():
    validate_url("http://github.com/jimsmith")


def test_validate_url_rejects_non_http_urls():
    with pytest.raises(ValueError):
        validate_url("mailto:jim@smith.org")


@pytest.mark.parametrize(
    "orcid_id", ["0000-0002-1825-0097", "0000-0001-5109-3700", "0000-0002-1694-233X"]
)
def test_validate_orcid_accepts_valid_ids(orcid_id):
    assert validate_orcid(orcid_id)


def test_validate_orcid_rejects_malformed_ids():
    with pytest.raises(ValueError):
        validate_orcid("not-an-orcid")


def test_validate_orcid_rejects_mismatching_check_digit():
    with pytest.raises(ValueError):
        validate_orcid("1000-0002-1825-0097")
