from unittest.mock import patch, sentinel

import pytest
from pyramid.httpexceptions import HTTPBadRequest

from h.exceptions import InvalidUserId
from h.traversal.user import UserByIDRoot, UserByNameRoot, UserRoot


@pytest.mark.usefixtures("user_service")
class TestUserRoot:
    def test_get_user_context(self, root, user_service, UserContext):
        user = root.get_user_context(sentinel.userid, sentinel.authority)

        user_service.fetch.assert_called_once_with(sentinel.userid, sentinel.authority)

        UserContext.assert_called_with(user_service.fetch.return_value)
        assert user == UserContext.return_value

    def test_get_user_context_raises_if_the_user_does_not_exist(
        self, root, user_service
    ):
        user_service.fetch.return_value = None

        with pytest.raises(KeyError):
            root.get_user_context(sentinel.userid, sentinel.authority)

    def test_get_user_context_raises_if_the_userid_is_invalid(self, root, user_service):
        user_service.fetch.side_effect = InvalidUserId("user_id")

        with pytest.raises(HTTPBadRequest):
            root.get_user_context(sentinel.bad_username, authority=None)

    @pytest.fixture(autouse=True)
    def UserContext(self, patch):
        return patch("h.traversal.user.UserContext")

    @pytest.fixture
    def root(self, pyramid_request):
        return UserRoot(pyramid_request)


@pytest.mark.usefixtures("user_service")
class TestUserByNameRoot:
    def test_it_fetches_the_requested_user(self, root, pyramid_request):
        context = root[sentinel.username]

        root.get_user_context.assert_called_once_with(
            sentinel.username, authority=pyramid_request.effective_authority
        )
        assert context == root.get_user_context.return_value

    @pytest.fixture
    def root(self, pyramid_request):
        root = UserByNameRoot(pyramid_request)

        with patch.object(root, "get_user_context"):
            yield root


@pytest.mark.usefixtures("user_service")
class TestUserByIDRoot:
    def test_it_fetches_the_requested_user(self, root):
        context = root[sentinel.userid]

        root.get_user_context.assert_called_once_with(sentinel.userid, authority=None)

        assert context == root.get_user_context.return_value

    @pytest.fixture
    def root(self, pyramid_request):
        root = UserByIDRoot(pyramid_request)
        with patch.object(root, "get_user_context"):
            yield root
