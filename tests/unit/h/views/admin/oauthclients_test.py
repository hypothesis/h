from unittest.mock import Mock, create_autospec, sentinel

import pytest
from pyramid.httpexceptions import HTTPNotFound

from h.models.auth_client import AuthClient, GrantType, ResponseType
from h.views.admin.oauthclients import (
    AuthClientCreateController,
    AuthClientEditController,
    index,
)


class FakeForm:
    """Fake implementation of `deform.form.Form`."""

    appstruct = None

    def set_appstruct(self, appstruct):
        self.appstruct = appstruct

    def render(self):
        return self.appstruct

    def validate(self, items):
        self.appstruct = {}
        for name, value in items:
            if name == "grant_type":
                value = GrantType[value]
            elif name == "response_type":
                value = ResponseType[value]
            self.appstruct[name] = value
        return self.appstruct


def test_index_lists_authclients_sorted_by_name(pyramid_request):
    clients = [
        AuthClient(authority="foo.org", name="foo"),
        AuthClient(authority="foo.org", name="bar"),
    ]
    for client in clients:
        pyramid_request.db.add(client)

    ctx = index(pyramid_request)

    expected_clients = [clients[1], clients[0]]
    assert ctx == {"clients": expected_clients}


@pytest.mark.usefixtures("routes")
class TestAuthClientCreateController:
    def test_get_sets_field_defaults(self, pyramid_request):
        ctrl = AuthClientCreateController(pyramid_request)

        ctx = ctrl.get()

        assert ctx["form"] == {
            "authority": "example.com",
            "grant_type": GrantType.authorization_code,
            "response_type": ResponseType.code,
            "trusted": False,
        }

    def test_post_creates_authclient(self, form_post, pyramid_request):
        pyramid_request.POST = form_post
        pyramid_request.POST["name"] = "Third Party App"
        ctrl = AuthClientCreateController(pyramid_request)

        ctrl.post()

        pyramid_request.db.query(AuthClient).filter_by(name="Third Party App").one()

    @pytest.mark.parametrize(
        "grant_type, expected_response_type",
        [("authorization_code", ResponseType.code), ("jwt_bearer", None)],
    )
    def test_post_sets_response_type(
        self, form_post, pyramid_request, grant_type, expected_response_type
    ):
        pyramid_request.POST = form_post
        pyramid_request.POST["grant_type"] = grant_type
        ctrl = AuthClientCreateController(pyramid_request)

        ctrl.post()

        client = pyramid_request.db.query(AuthClient).one()
        assert client.response_type == expected_response_type

    def test_post_generates_secret_for_jwt_clients(self, form_post, pyramid_request):
        pyramid_request.POST = form_post
        pyramid_request.POST["grant_type"] = "jwt_bearer"
        secret_gen = Mock(return_value="keep-me-secret")
        ctrl = AuthClientCreateController(pyramid_request, secret_gen=secret_gen)

        ctrl.post()

        client = pyramid_request.db.query(AuthClient).one()
        assert client.secret == "keep-me-secret"

    def test_post_generates_secret_for_client_credentials_clients(
        self, form_post, pyramid_request
    ):
        pyramid_request.POST = form_post
        pyramid_request.POST["grant_type"] = "client_credentials"
        secret_gen = Mock(return_value="keep-me-secret")
        ctrl = AuthClientCreateController(pyramid_request, secret_gen=secret_gen)

        ctrl.post()

        client = pyramid_request.db.query(AuthClient).one()
        assert client.secret == "keep-me-secret"

    def test_post_does_not_generate_secret_for_authcode_clients(
        self, form_post, pyramid_request
    ):
        pyramid_request.POST = form_post
        pyramid_request.POST["grant_type"] = "authorization_code"
        ctrl = AuthClientCreateController(pyramid_request)

        ctrl.post()

        client = pyramid_request.db.query(AuthClient).one()
        assert client.secret is None

    def test_post_redirects_to_edit_view(self, form_post, matchers, pyramid_request):
        pyramid_request.POST = form_post
        ctrl = AuthClientCreateController(pyramid_request)

        response = ctrl.post()

        client = pyramid_request.db.query(AuthClient).one()
        expected_location = pyramid_request.route_url(
            "admin.oauthclients_edit", id=client.id
        )
        assert response == matchers.Redirect302To(expected_location)


@pytest.mark.usefixtures("routes")
class TestAuthClientEditController:
    def test_it_gets_the_client_from_the_id(self, pyramid_request, auth_client):
        controller = AuthClientEditController(sentinel.context, pyramid_request)

        assert controller.client == auth_client

    def test_it_returns_HTTPNotFound_if_the_client_is_missing(
        self, pyramid_request, db_session, auth_client
    ):
        db_session.delete(auth_client)

        with pytest.raises(HTTPNotFound):
            AuthClientEditController(sentinel.context, pyramid_request)

    def test_it_returns_HTTPNotFound_if_the_client_id_is_invalid(self, pyramid_request):
        pyramid_request.matchdict["id"] = "scrambled_id"

        with pytest.raises(HTTPNotFound):
            AuthClientEditController(sentinel.context, pyramid_request)

    def test_read(self, pyramid_request, auth_client):
        controller = AuthClientEditController(sentinel.context, pyramid_request)

        response = controller.read()

        assert response["form"] == self._expected_form(auth_client)

    def test_update_updates_auth_client(self, auth_client, form_post, pyramid_request):
        form_post["client_id"] = auth_client.id
        form_post["client_secret"] = auth_client.secret
        pyramid_request.POST = form_post
        controller = AuthClientEditController(sentinel.context, pyramid_request)

        response = controller.update()

        assert auth_client.name == "new-name"
        assert response["form"] == self._expected_form(auth_client)

    @pytest.mark.parametrize(
        "grant_type,expected_type",
        [("authorization_code", ResponseType.code), ("jwt_bearer", None)],
    )
    def test_update_sets_response_type(
        self, auth_client, form_post, pyramid_request, grant_type, expected_type
    ):
        pyramid_request.POST = form_post
        pyramid_request.POST["grant_type"] = grant_type
        controller = AuthClientEditController(sentinel.context, pyramid_request)

        controller.update()

        assert auth_client.response_type == expected_type

    def test_update_does_not_update_read_only_fields(
        self, auth_client, form_post, pyramid_request
    ):
        # Attempt to modify read-only ID and secret fields.
        old_id = auth_client.id
        old_secret = auth_client.secret
        form_post["client_id"] = "new-id"
        form_post["client_secret"] = "new-secret"
        pyramid_request.POST = form_post
        controller = AuthClientEditController(sentinel.context, pyramid_request)

        response = controller.update()

        assert auth_client.id == old_id
        assert auth_client.secret == old_secret
        assert response["form"] == self._expected_form(auth_client)

    def test_delete_removes_auth_client(self, auth_client, pyramid_request):
        pyramid_request.db.delete = create_autospec(
            pyramid_request.db.delete, return_value=None
        )
        controller = AuthClientEditController(sentinel.context, pyramid_request)

        controller.delete()

        pyramid_request.db.delete.assert_called_with(auth_client)

    def test_delete_redirects_to_index(self, matchers, pyramid_request):
        pyramid_request.db.delete = create_autospec(
            pyramid_request.db.delete, return_value=None
        )
        controller = AuthClientEditController(sentinel.context, pyramid_request)

        response = controller.delete()

        expected_location = pyramid_request.route_url("admin.oauthclients")
        assert response == matchers.Redirect302To(expected_location)

    def _expected_form(self, auth_client):
        return {
            "authority": auth_client.authority,
            "name": auth_client.name,
            "client_id": auth_client.id,
            "client_secret": auth_client.secret,
            "redirect_url": auth_client.redirect_uri or "",
            "trusted": auth_client.trusted,
            "grant_type": auth_client.grant_type,
            "response_type": auth_client.response_type,
        }

    @pytest.fixture
    def pyramid_request(self, pyramid_request, auth_client):
        pyramid_request.matchdict["id"] = auth_client.id
        return pyramid_request

    @pytest.fixture
    def auth_client(self, factories):
        return factories.AuthClient(
            name="testclient",
            authority="annotator.org",
            secret="not_a_secret",
            trusted=False,
            grant_type=GrantType.authorization_code,
            response_type=ResponseType.code,
        )


@pytest.fixture
def form_post():
    """POST data fixture for submission of authclient create and edit forms."""
    return {
        "name": "new-name",
        "authority": "newauth.org",
        "grant_type": "authorization_code",
        "response_type": "code",
        "redirect_url": "https://newurl.org/receive_auth",
        "trusted": False,
    }


@pytest.fixture
def pyramid_request(pyramid_request):
    pyramid_request.session = Mock(spec_set=["flash", "get_csrf_token"])
    pyramid_request.create_form.return_value = FakeForm()
    return pyramid_request


@pytest.fixture
def routes(pyramid_config):
    pyramid_config.add_route("admin.oauthclients", "/admin/oauthclients")
    pyramid_config.add_route("admin.oauthclients_create", "/admin/oauthclients/new")
    pyramid_config.add_route("admin.oauthclients_edit", "/admin/oauthclients/{id}")
