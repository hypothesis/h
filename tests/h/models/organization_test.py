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
        authority='example.com',
        )

    assert organization.name == 'My organization'
    assert organization.logo == logo
    assert organization.authority == 'example.com'


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


def test_repr(db_session, factories):
    organization = models.Organization(name='My Organization', authority='example.com')
    db_session.add(organization)
    db_session.flush()

    assert organization.id is not None
    assert organization.pubid is not None
    assert repr(organization) == "<Organization: my-organization>"
