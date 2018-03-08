# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest
from h import models


def test_init_sets_given_attributes():
    logo = """<svg width="100" height="100">
            <circle cx="50" cy="50" r="40" stroke="green" stroke-width="4" fill="yellow" />
            </svg>"""
    organization = models.Organization(
        name='My organization',
        logo=logo,
        )

    assert organization.name == 'My organization'
    assert organization.logo == logo


def test_null_logo():
    organization = models.Organization(name="My Organization")

    assert organization.name == 'My Organization'
    assert organization.logo is None


def test_slug():
    organization = models.Organization(name="My Organization")

    assert organization.slug == 'my-organization'


def test_too_short_name_raises_value_error():
    with pytest.raises(ValueError):
        models.Organization(name="")


def test_too_long_name_raises_value_error():
    with pytest.raises(ValueError):
        models.Organization(name="abcdefghijklmnopqrstuvwxyz")


def test_too_long_logo_raises_value_error():
    with pytest.raises(ValueError):
        models.Organization(logo='<svg>{}</svg>'.format("abcdefghijklmnopqrstuvwxyz" * 400))


def test_malformed_logo_raises_value_error():
    with pytest.raises(ValueError):
        models.Organization(logo='<svg>/svg>')


def test_non_svg_logo_raises_value_error():
    with pytest.raises(ValueError):
        models.Organization(logo='<h>This is not a svg</h>')


def test_repr(db_session, factories):
    name = "My Organization"

    organization = models.Organization(name=name)
    db_session.add(organization)
    db_session.flush()

    organization.id is not None
    assert repr(organization) == "<Organization: my-organization>"
