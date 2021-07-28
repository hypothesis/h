import pytest
from pyramid.authorization import ACLAuthorizationPolicy


@pytest.fixture
def set_permissions(pyramid_config):
    def request_with_permissions(user_id, principals):
        pyramid_config.testing_securitypolicy(user_id, groupids=principals)
        pyramid_config.set_authorization_policy(ACLAuthorizationPolicy())

    return request_with_permissions
