# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest
from mock import Mock

import colander

from h.schemas.forms.accounts import validators
from h.services.user import UserService


@pytest.mark.usefixtures('user_model')
class TestUniqueEmail(object):

    def test_it_proxies_user_lookup_to_user_service(self,
                                                    dummy_node,
                                                    pyramid_request,
                                                    user_model):
        with pytest.raises(colander.Invalid):
            validators.unique_email(dummy_node, "foo@bar.com")

        user_model.get_by_email.assert_called_with(pyramid_request.db,
                                                   "foo@bar.com",
                                                   pyramid_request.default_authority)

    def test_it_is_invalid_when_user_exists(self, dummy_node):
        pytest.raises(colander.Invalid,
                      validators.unique_email,
                      dummy_node,
                      "foo@bar.com")

    def test_it_is_valid_when_user_does_not_exist(self,
                                                  dummy_node,
                                                  user_model):
        user_model.get_by_email.return_value = None

        assert validators.unique_email(dummy_node, "foo@bar.com") is None

    def test_it_is_valid_when_authorized_users_email(self,
                                                     dummy_node,
                                                     pyramid_config,
                                                     user_model):
        """
        If the given email is the authorized user's current email it's valid.

        This is so that we don't get a "That email is already taken" validation
        error when a user tries to change their email address to the same email
        address that they already have it set to.

        """
        pyramid_config.testing_securitypolicy('acct:elliot@hypothes.is')
        user_model.get_by_email.return_value = Mock(
            spec_set=('userid',),
            userid='acct:elliot@hypothes.is')

        validators.unique_email(dummy_node, "elliot@bar.com")


@pytest.fixture
def dummy_node(pyramid_request):
    class DummyNode(object):
        def __init__(self, request):
            self.bindings = {
                'request': request
            }
    return DummyNode(pyramid_request)


@pytest.fixture
def user_model(patch):
    return patch('h.schemas.forms.accounts.validators.models.User')


@pytest.fixture
def user_service(db_session, pyramid_config):
    service = Mock(spec_set=UserService(default_authority='example.com',
                                        session=db_session))
    service.fetch_for_login.return_value = None
    pyramid_config.register_service(service, name='user')
    return service
