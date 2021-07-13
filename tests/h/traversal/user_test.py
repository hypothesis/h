from unittest.mock import sentinel

import pytest
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.httpexceptions import HTTPBadRequest

from h.auth import role
from h.exceptions import InvalidUserId
from h.traversal.user import UserByIDRoot, UserByNameRoot, UserContext, UserRoot


class TestUserContext:
    def test_acl_matching_authority_allows_read(self, factories):
        user = factories.User()

        context = UserContext(user)

        policy = ACLAuthorizationPolicy()
        assert policy.permits(context, [f"client_authority:{user.authority}"], "read")
        assert not policy.permits(
            context, ["client_authority:DIFFERENT_AUTHORITY"], "read"
        )


@pytest.mark.usefixtures("user_service")
class TestUserRoot:
    @pytest.mark.parametrize(
        "principals,has_create", (([], False), ([role.AuthClient], True))
    )
    def test_it_does_not_assign_create_permission_without_auth_client_role(
        self, pyramid_request, set_permissions, principals, has_create
    ):
        set_permissions(user_id="*any*", principals=principals)

        context = UserRoot(pyramid_request)

        assert bool(pyramid_request.has_permission("create", context)) == has_create


@pytest.mark.usefixtures("user_service")
class TestUserByNameRoot:
    def test_it_fetches_the_requested_user(
        self, pyramid_request, root, user_service, client_authority
    ):
        client_authority.return_value = sentinel.client_authority

        user = root[sentinel.username]

        client_authority.assert_called_once_with(pyramid_request)
        user_service.fetch.assert_called_once_with(
            sentinel.username, sentinel.client_authority
        )
        assert user == user_service.fetch.return_value

    def test_it_uses_the_default_authority_when_theres_no_client_one(
        self, root, user_service, pyramid_request, client_authority
    ):
        client_authority.return_value = None

        root[sentinel.username]

        user_service.fetch.assert_called_once_with(
            sentinel.username, pyramid_request.default_authority
        )

    def test_it_raises_KeyError_if_the_user_does_not_exist(self, root, user_service):
        user_service.fetch.return_value = None

        with pytest.raises(KeyError):
            root["does_not_exist"]

    @pytest.fixture(autouse=True)
    def client_authority(self, patch):
        return patch("h.traversal.user.client_authority")

    @pytest.fixture
    def root(self, pyramid_request):
        return UserByNameRoot(pyramid_request)


@pytest.mark.usefixtures("user_service")
class TestUserByIDRoot:
    def test_it_fetches_the_requested_user(self, root, user_service, UserContext):
        context = root[sentinel.userid]

        user_service.fetch.assert_called_once_with(sentinel.userid)
        UserContext.assert_called_with(user_service.fetch.return_value)
        assert context == UserContext.return_value

    def test_it_fails_with_bad_request_if_the_userid_is_invalid(
        self, root, user_service
    ):
        user_service.fetch.side_effect = InvalidUserId("dummy id")

        with pytest.raises(HTTPBadRequest):
            root["total_nonsense"]

    def test_it_raises_KeyError_if_the_user_does_not_exist(self, root, user_service):
        user_service.fetch.return_value = None

        with pytest.raises(KeyError):
            root["does_not_exist"]

    @pytest.fixture
    def root(self, pyramid_request):
        return UserByIDRoot(pyramid_request)

    @pytest.fixture(autouse=True)
    def UserContext(self, patch):
        return patch("h.traversal.user.UserContext")
