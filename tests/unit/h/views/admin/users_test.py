from datetime import datetime
from unittest import mock

import pytest
from pyramid import httpexceptions

from h.models import Annotation
from h.services.user_delete import UserDeleteService
from h.views.admin.users import (
    UserNotFoundError,
    format_date,
    user_not_found,
    users_activate,
    users_delete,
    users_index,
)

users_index_fixtures = pytest.mark.usefixtures("models", "annotation_stats_service")


@pytest.mark.parametrize(
    "input_date,expected",
    ((datetime(2001, 11, 29, 21, 50, 59, 999999), "2001-11-29 21:50"), (None, "")),
)
def test_format_date(input_date, expected):
    assert format_date(input_date) == expected


@users_index_fixtures
def test_users_index(pyramid_request):
    result = users_index(pyramid_request)

    assert result == {
        "default_authority": pyramid_request.default_authority,
        "username": None,
        "authority": None,
        "user": None,
        "user_meta": {},
        "format_date": format_date,
    }


@users_index_fixtures
def test_users_index_looks_up_users_by_username(models, pyramid_request):
    pyramid_request.params = {"username": "bob", "authority": "foo.org"}
    models.User.get_by_username.return_value = None
    models.User.get_by_email.return_value = None

    users_index(pyramid_request)

    models.User.get_by_username.assert_called_with(pyramid_request.db, "bob", "foo.org")


@users_index_fixtures
def test_users_index_looks_up_users_by_email(models, pyramid_request):
    pyramid_request.params = {"username": "bob@builder.com", "authority": "foo.org"}
    models.User.get_by_username.return_value = None
    models.User.get_by_email.return_value = None

    users_index(pyramid_request)

    models.User.get_by_email.assert_called_with(
        pyramid_request.db, "bob@builder.com", "foo.org"
    )


@users_index_fixtures
def test_users_index_strips_spaces(models, pyramid_request):
    pyramid_request.params = {"username": "    bob   ", "authority": "   foo.org    "}
    models.User.get_by_username.return_value = None
    models.User.get_by_email.return_value = None

    users_index(pyramid_request)

    models.User.get_by_username.assert_called_with(pyramid_request.db, "bob", "foo.org")


@users_index_fixtures
def test_users_index_no_user_found(models, pyramid_request):
    pyramid_request.params = {"username": "bob", "authority": "foo.org"}
    models.User.get_by_username.return_value = None
    models.User.get_by_email.return_value = None

    result = users_index(pyramid_request)

    assert result == {
        "default_authority": "example.com",
        "username": "bob",
        "authority": "foo.org",
        "user": None,
        "user_meta": {},
        "format_date": format_date,
    }


@users_index_fixtures
def test_users_index_user_marked_as_deleted(models, pyramid_request, factories):
    pyramid_request.params = {"username": "bob", "authority": "foo.org"}
    user = factories.User.build(username="bob", authority="foo.org", deleted=True)
    models.User.get_by_username.return_value = user

    result = users_index(pyramid_request)

    assert result == {
        "default_authority": "example.com",
        "username": "bob",
        "authority": "foo.org",
        "user": None,
        "user_meta": {},
        "format_date": format_date,
    }


@users_index_fixtures
def test_users_index_user_found(
    models, pyramid_request, factories, annotation_stats_service
):
    pyramid_request.params = {"username": "bob", "authority": "foo.org"}
    user = factories.User.build(username="bob", authority="foo.org")
    models.User.get_by_username.return_value = user
    annotation_stats_service.total_user_annotation_count.return_value = 8

    result = users_index(pyramid_request)

    assert result == {
        "default_authority": "example.com",
        "username": "bob",
        "authority": "foo.org",
        "user": user,
        "user_meta": {"annotations_count": 8},
        "format_date": format_date,
    }


users_activate_fixtures = pytest.mark.usefixtures("user_service", "ActivationEvent")


@users_activate_fixtures
def test_users_activate(user_service, pyramid_request, notify, ActivationEvent):
    pyramid_request.params = {"userid": "acct:bob@example.org"}

    result = users_activate(pyramid_request)

    user_service.fetch.assert_called_once_with("acct:bob@example.org")
    user_service.fetch.return_value.activate.assert_called_once_with()
    assert pyramid_request.session.peek_flash("success")

    ActivationEvent.assert_called_once_with(
        pyramid_request, user_service.fetch.return_value
    )
    notify.assert_called_with(ActivationEvent.return_value)
    assert isinstance(result, httpexceptions.HTTPFound)


@users_activate_fixtures
def test_users_activate_user_not_found_error(user_service, pyramid_request):
    pyramid_request.params = {"userid": "acct:bob@foo.org"}
    user_service.fetch.return_value = None

    with pytest.raises(UserNotFoundError):
        users_activate(pyramid_request)


def test_users_delete_user_not_found_error(user_service, pyramid_request):
    pyramid_request.params = {"userid": "acct:bob@foo.org"}

    user_service.fetch.return_value = None

    with pytest.raises(UserNotFoundError):
        users_delete(pyramid_request)


def test_user_not_found_view(pyramid_request):
    result = user_not_found(UserNotFoundError("error"), pyramid_request)

    assert pyramid_request.session.peek_flash("error")
    assert isinstance(result, httpexceptions.HTTPFound)


def test_users_delete_deletes_user(user_service, user_delete_service, pyramid_request):
    pyramid_request.params = {"userid": "acct:bob@example.com"}
    user = mock.MagicMock()

    user_service.fetch.return_value = user

    users_delete(pyramid_request)

    user_delete_service.delete_user.assert_called_once_with(
        user,
        requested_by=pyramid_request.user,
        tag=pyramid_request.matched_route.name,
    )


@pytest.fixture(autouse=True)
def routes(pyramid_config):
    pyramid_config.add_route("admin.users", "/adm/users")


@pytest.fixture
def ActivationEvent(patch):
    return patch("h.views.admin.users.ActivationEvent")


@pytest.fixture
def models(patch):
    module = patch("h.views.admin.users.models")
    module.Annotation = Annotation
    return module


@pytest.fixture
def annotation_stats_service(annotation_stats_service):
    annotation_stats_service.total_user_annotation_count.return_value = 0
    return annotation_stats_service


@pytest.fixture
def user_delete_service(pyramid_config, pyramid_request):
    service = mock.create_autospec(UserDeleteService, instance=True, spec_set=True)
    service.return_value.request = pyramid_request
    pyramid_config.register_service(service, name="user_delete")
    return service
