# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from h.services import authority_group


def test_returns_world_group_for_matching_domain(svc):
    public_groups = svc.public_groups('example.com')

    assert [group.pubid for group in public_groups] == ['__world__']


def test_excludes_world_group_for_non_matching_domain(svc):
    public_groups = svc.public_groups('partner.org')

    assert '__world__' not in [group.pubid for group in public_groups]


def test_returns_public_groups_for_non_matching_domain(svc, publisher_group):
    assert publisher_group in svc.public_groups('partner.org')


def test_excludes_third_party_private_groups(svc, third_party_private_group):
    assert third_party_private_group not in svc.public_groups('partner.org')


def test_excludes_private_groups(svc, private_group):
    assert private_group not in svc.public_groups('partner.org')


@pytest.fixture
def svc(db_session):
    return authority_group.AuthorityGroupService(db_session, 'example.com')


@pytest.fixture
def private_group(factories):
    return factories.Group(authority='example.com')


@pytest.fixture
def publisher_group(factories):
    return factories.PublisherGroup(authority='partner.org')


@pytest.fixture
def third_party_private_group(factories):
    return factories.Group(authority='partner.org')
