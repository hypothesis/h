import pytest

from h.accounts.util import validate_url


def test_validate_url_rejects_urls_without_domains():
    with pytest.raises(ValueError):  # noqa: PT011
        validate_url("http:///path")


def test_validate_url_adds_http_prefix():
    assert validate_url("github.com/jimsmith") == "http://github.com/jimsmith"


def test_validate_url_accepts_http_urls():
    validate_url("http://github.com/jimsmith")


def test_validate_url_rejects_non_http_urls():
    with pytest.raises(ValueError):  # noqa: PT011
        validate_url("mailto:jim@smith.org")
