# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from h.services.list_organizations import ListOrganizationsService
from h.services.list_organizations import list_organizations_factory
from h.services.organization import organization_factory
from h.models import Organization


class TestListOrganizations(object):
    def test_returns_organizations_from_all_authorities_if_no_authority_specified(
        self, svc, organizations, default_orgs, alternate_organizations
    ):
        expected_orgs = default_orgs + organizations + alternate_organizations

        results = svc.organizations()

        assert results == expected_orgs

    def test_returns_organizations_for_the_authority_specified(
        self,
        svc,
        authority,
        organizations,
        alternate_organizations,
        alternate_authority,
    ):

        results = svc.organizations(authority=alternate_authority)

        assert results == alternate_organizations


class TestListOrganizationsFactory(object):
    def test_list_organizations_factory(self, pyramid_request):
        svc = list_organizations_factory(None, pyramid_request)

        assert isinstance(svc, ListOrganizationsService)

    def test_provides_request_db_as_session(self, pyramid_request):
        svc = list_organizations_factory(None, pyramid_request)

        assert svc._session == pyramid_request.db


@pytest.fixture
def authority(pyramid_request):
    return pyramid_request.default_authority


@pytest.fixture
def alternate_authority():
    return "bar.com"


@pytest.fixture
def org_svc(pyramid_request):
    return organization_factory(None, pyramid_request)


@pytest.fixture
def organizations(factories, authority, org_svc):
    # Add these out of order so it will come back out of order if unsorted..
    org2 = org_svc.create(name="Org2", authority=authority)
    org1 = org_svc.create(name="Org1", authority=authority)
    return [org1, org2]


@pytest.fixture
def alternate_organizations(factories, alternate_authority, org_svc):
    # Add these out of order so it will come back out of order if unsorted..
    org4 = org_svc.create(name="Org4", authority=alternate_authority)
    org3 = org_svc.create(name="Org3", authority=alternate_authority)
    return [org3, org4]


@pytest.fixture
def default_orgs(db_session):
    return [Organization.default(db_session)]


@pytest.fixture
def svc(db_session):
    return ListOrganizationsService(session=db_session)
