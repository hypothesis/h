import pyramid.authorization
import pytest
from pyramid import security
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.httpexceptions import HTTPBadRequest

from h.auth import role
from h.exceptions import InvalidUserId
from h.traversal.user import UserContext, UserRoot, UserUserIDRoot


class TestUserContext:
    def test_acl_assigns_read_to_AuthClient_with_user_authority(self, factories):
        user = factories.User(username="fiona", authority="myauthority.com")
        res = UserContext(user)
        actual = res.__acl__()
        expect = [(security.Allow, "client_authority:myauthority.com", "read")]
        assert actual == expect

    def test_acl_matching_authority_allows_read(self, factories):
        policy = ACLAuthorizationPolicy()

        user = factories.User(username="fiona", authority="myauthority.com")
        res = UserContext(user)

        assert policy.permits(res, ["client_authority:myauthority.com"], "read")
        assert not policy.permits(res, ["client_authority:example.com"], "read")


@pytest.mark.usefixtures("user_service", "client_authority")
class TestUserRoot:
    def test_it_does_not_assign_create_permission_without_auth_client_role(
        self, pyramid_config, pyramid_request
    ):
        policy = pyramid.authorization.ACLAuthorizationPolicy()
        pyramid_config.testing_securitypolicy("acct:adminuser@foo")
        pyramid_config.set_authorization_policy(policy)

        context = UserRoot(pyramid_request)

        assert not pyramid_request.has_permission("create", context)

    def test_it_assigns_create_permission_to_auth_client_role(
        self, set_permissions, pyramid_request
    ):
        set_permissions("acct:adminuser@foo", principals=[role.AuthClient])

        context = UserRoot(pyramid_request)

        assert pyramid_request.has_permission("create", context)

    def test_it_fetches_the_requested_user(
        self, pyramid_request, user_factory, user_service
    ):
        user_factory["bob"]

        user_service.fetch.assert_called_once_with(
            "bob", pyramid_request.default_authority
        )

    def test_it_proxies_to_client_authority(
        self, pyramid_request, user_factory, client_authority, user_service
    ):
        user_factory["bob"]

        client_authority.assert_called_once_with(pyramid_request)
        user_service.fetch.assert_called_once_with(
            "bob", pyramid_request.default_authority
        )

    def test_it_fetches_with_client_authority_if_present(
        self, pyramid_request, user_factory, client_authority, user_service
    ):
        client_authority.return_value = "something.com"
        user_factory["bob"]

        user_service.fetch.assert_called_once_with("bob", client_authority.return_value)

    def test_it_raises_KeyError_if_the_user_does_not_exist(
        self, user_factory, user_service
    ):
        user_service.fetch.return_value = None

        with pytest.raises(KeyError):
            user_factory["does_not_exist"]

    def test_it_returns_users(self, factories, user_factory, user_service):
        user_service.fetch.return_value = user = factories.User.build()

        assert user_factory[user.username] == user

    @pytest.fixture
    def user_factory(self, pyramid_request):
        return UserRoot(pyramid_request)


@pytest.mark.usefixtures("user_service")
class TestUserUserIDRoot:
    def test_it_fetches_the_requested_user(
        self, pyramid_request, user_userid_root, user_service
    ):
        user_userid_root["acct:bob@example.com"]

        user_service.fetch.assert_called_once_with("acct:bob@example.com")

    def test_it_fails_with_bad_request_if_the_userid_is_invalid(
        self, pyramid_request, user_userid_root, user_service
    ):
        user_service.fetch.side_effect = InvalidUserId("dummy id")

        with pytest.raises(HTTPBadRequest):
            user_userid_root["total_nonsense"]

    def test_it_raises_KeyError_if_the_user_does_not_exist(
        self, user_userid_root, user_service
    ):
        user_service.fetch.return_value = None

        with pytest.raises(KeyError):
            user_userid_root["does_not_exist"]

    def test_it_returns_UserContexts(self, factories, user_userid_root, user_service):
        user_service.fetch.return_value = user = factories.User.build()

        resource = user_userid_root[user.username]

        assert isinstance(resource, UserContext)

    @pytest.fixture
    def user_userid_root(self, pyramid_request):
        return UserUserIDRoot(pyramid_request)


@pytest.fixture
def client_authority(patch):
    client_authority = patch("h.traversal.user.client_authority")
    client_authority.return_value = None
    return client_authority
