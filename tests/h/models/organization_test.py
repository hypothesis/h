import pytest

from h import models


def test_init_sets_given_attributes():
    logo = """<svg width="100" height="100" xmlns="http://www.w3.org/2000/svg">
            <circle cx="50" cy="50" r="40" stroke="green" stroke-width="4" fill="yellow" />
            </svg>"""
    organization = models.Organization(
        name="My organization", logo=logo, authority="example.com"
    )

    assert organization.name == "My organization"
    assert organization.logo == logo
    assert organization.authority == "example.com"


def test_null_logo():
    organization = models.Organization(name="My Organization")

    assert organization.name == "My Organization"
    assert organization.logo is None


def test_too_short_name_raises_value_error():
    with pytest.raises(ValueError):
        models.Organization(name="")


def test_too_long_name_raises_value_error():
    with pytest.raises(ValueError):
        models.Organization(name="abcdefghijklmnopqrstuvwxyz")


def test_none_logo_is_valid():
    org = models.Organization(name="My Organization", logo=None)
    assert org.logo is None


def test_repr():
    organization = models.Organization(
        name="My Organization", authority="example.com", pubid="test_pubid"
    )

    assert repr(organization) == "<Organization: test_pubid>"


@pytest.mark.parametrize(
    "pubid,is_default",
    ((models.Organization.DEFAULT_PUBID, True), ("anything_else", False)),
)
def test_is_default(pubid, is_default):
    organization = models.Organization(pubid=pubid)

    assert organization.is_default == is_default
