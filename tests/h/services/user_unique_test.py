# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from h.services.user_unique import UserUniqueService, user_unique_factory
from h.services.user_unique import DuplicateUserError


class TestUserUniqueEnsureUnique(object):
    def test_it_raises_if_email_uniqueness_violated(self, svc, user, pyramid_request):
        dupe_email = user.email
        with pytest.raises(DuplicateUserError,
                           match=(".*user with email address {} already exists".format(dupe_email))):
            svc.ensure_unique({'email': dupe_email},
                              authority=pyramid_request.authority)

    def test_it_allows_duplicate_email_at_different_authority(self, svc, user, pyramid_request):
        svc.ensure_unique({'email': user.email}, authority='foo.com')

    def test_it_raises_if_username_uniqueness_violated(self, svc, user, pyramid_request):
        dupe_username = user.username
        with pytest.raises(DuplicateUserError,
                           match=(".*user with username {} already exists".format(dupe_username))):
            svc.ensure_unique({'username': dupe_username},
                              authority=pyramid_request.authority)

    def test_it_allows_duplicate_username_at_different_authority(self, svc, user, pyramid_request):
        svc.ensure_unique({'username': user.username}, authority='foo.com')


class TestUserUniqueFactory(object):

    def test_user_unique_factory(self, pyramid_request):
        svc = user_unique_factory(None, pyramid_request)

        assert isinstance(svc, UserUniqueService)

    def test_uses_request_authority(self, pyramid_request):
        pyramid_request.authority = 'bar.com'

        svc = user_unique_factory(None, pyramid_request)

        assert svc.request_authority == 'bar.com'


@pytest.fixture
def user(factories, pyramid_request):
    return factories.User(
        username="fernando",
        email="foo@example.com",
        authority=pyramid_request.authority
    )


@pytest.fixture
def svc(pyramid_request, db_session):
    return UserUniqueService(
        session=db_session,
        request_authority=pyramid_request.authority
    )
