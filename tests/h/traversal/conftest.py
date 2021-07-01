import pyramid.authorization
import pyramid.security
import pytest


@pytest.fixture
def set_permissions(pyramid_config):
    default = object()

    def request_with_permissions(user_id=None, principals=default):
        if principals is default:
            principals = [pyramid.security.Everyone]

        policy = pyramid.authorization.ACLAuthorizationPolicy()
        pyramid_config.testing_securitypolicy(user_id, groupids=principals)
        pyramid_config.set_authorization_policy(policy)

    return request_with_permissions
