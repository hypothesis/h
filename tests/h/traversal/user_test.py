from unittest.mock import patch, sentinel

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

    def test_get_user(self, root, user_service):
        user = root.get_user(sentinel.userid, sentinel.authority)

        user_service.fetch.assert_called_once_with(sentinel.userid, sentinel.authority)

        assert user == user_service.fetch.return_value

    def test_get_user_raises_if_the_user_does_not_exist(self, root, user_service):
        user_service.fetch.return_value = None

        with pytest.raises(KeyError):
            root.get_user(sentinel.userid, sentinel.authority)

    def test_get_user_raises_if_the_userid_is_invalid(self, root, user_service):
        user_service.fetch.side_effect = InvalidUserId("user_id")

        with pytest.raises(HTTPBadRequest):
            root.get_user(sentinel.bad_username, authority=None)

    @pytest.fixture
    def root(self, pyramid_request):
        return UserRoot(pyramid_request)


@pytest.mark.usefixtures("user_service")
class TestUserByNameRoot:
    @pytest.mark.parametrize("returned_authority", (None, sentinel.client_authority))
    def test_it_fetches_the_requested_user(
        self, pyramid_request, root, user_service, client_authority, returned_authority
    ):
        client_authority.return_value = returned_authority

        user = root[sentinel.username]

        client_authority.assert_called_once_with(pyramid_request)
        root.get_user.assert_called_once_with(
            sentinel.username,
            authority=client_authority.return_value
            or pyramid_request.default_authority,
        )

        assert user == root.get_user.return_value

    @pytest.fixture(autouse=True)
    def client_authority(self, patch):
        return patch("h.traversal.user.client_authority")

    @pytest.fixture
    def root(self, pyramid_request):
        root = UserByNameRoot(pyramid_request)

        with patch.object(root, "get_user"):
            yield root


@pytest.mark.usefixtures("user_service")
class TestUserByIDRoot:
    def test_it_fetches_the_requested_user(self, root, user_service, UserContext):
        context = root[sentinel.userid]

        root.get_user.assert_called_once_with(sentinel.userid, authority=None)
        UserContext.assert_called_with(root.get_user.return_value)
        assert context == UserContext.return_value

    @pytest.fixture
    def root(self, pyramid_request):
        root = UserByIDRoot(pyramid_request)
        with patch.object(root, "get_user"):
            yield root

    @pytest.fixture(autouse=True)
    def UserContext(self, patch):
        return patch("h.traversal.user.UserContext")
