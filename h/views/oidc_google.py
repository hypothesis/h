import functools
import secrets
from os import environ
from urllib.parse import urlencode, urlunparse

import jwt
import requests
from pyramid.httpexceptions import HTTPForbidden, HTTPFound
from pyramid.view import view_config, view_defaults

from h.models.user_identity import IdentityProvider, UserIdentity
from h.services import JWTService, OpenIDClientService

from h.views.helpers import login


@view_defaults(request_method="GET")
class GoogleConnectAndLoginViews:
    def __init__(self, request) -> None:
        self.request = request

    @view_config(is_authenticated=True, route_name="oidc.connect.google")
    @view_config(is_authenticated=False, route_name="oidc.login.google")
    def connect_or_login(self):
        client_id = environ["GOOGLE_OIDC_CLIENT_ID"]
        state_signing_key = environ["GOOGLE_OIDC_STATE_SIGNING_KEY"]

        actions = {"oidc.connect.google": "connect", "oidc.login.google": "login"}
        action = actions[self.request.matched_route.name]

        state = jwt.encode(
            {"action": action, "rfp": secrets.token_hex()},
            state_signing_key,
            algorithm="HS256",
        )
        self.request.session["oidc.state.google"] = state

        return HTTPFound(
            location=urlunparse(
                (
                    "https",
                    "accounts.google.com",
                    "/o/oauth2/v2/auth",
                    "",
                    urlencode(
                        {
                            "client_id": client_id,
                            "response_type": "code",
                            "redirect_uri": self.request.route_url(
                                "oidc.redirect.google"
                            ),
                            "state": state,
                            "scope": "openid email",
                        }
                    ),
                    "",
                )
            )
        )


@view_defaults(request_method="GET", route_name="oidc.redirect.google")
class GoogleRedirectViews:
    def __init__(self, request) -> None:
        self.request = request
        self.openid_client = request.find_service(OpenIDClientService)
        self.user_service = request.find_service(name="user")

    @view_config()
    def redirect(self):
        state_signing_key = environ["GOOGLE_OIDC_STATE_SIGNING_KEY"]

        decoded_state = jwt.decode(
            self.request.params["state"], state_signing_key, algorithms=["HS256"]
        )

        action_str = decoded_state["action"]

        if action_str == "connect" and not self.request.is_authenticated:
            # You must be logged in to connect an identity to your existing
            # Hypothesis account.
            raise HTTPForbidden

        if action_str == "login" and self.request.is_authenticated:
            # You must be logged out in order to log in.
            raise HTTPForbidden

        token_url_response = requests.post(  # noqa: S113
            "https://oauth2.googleapis.com/token",
            params={
                "code": self.request.params["code"],
                "client_id": environ["GOOGLE_OIDC_CLIENT_ID"],
                "client_secret": environ["GOOGLE_OIDC_CLIENT_SECRET"],
                "redirect_uri": self.request.route_url("oidc.redirect.google"),
                "grant_type": "authorization_code",
            },
        )

        id_token = token_url_response.json()["id_token"]

        decoded_id_token = JWTService.decode_token(
            id_token, "https://www.googleapis.com/oauth2/v3/certs", ["RS256"]
        )

        google_id = decoded_id_token["sub"]
        breakpoint()

        user = self.user_service.fetch_by_identity(IdentityProvider.GOOGLE, google_id)

        actions = {
            "connect": functools.partial(self.connect_google_id, google_id, user),
            "login": functools.partial(self.log_in_with_google, google_id, user),
        }
        action_method = actions[action_str]
        return action_method()

    def connect_google_id(self, google_id: str, user):
        if user and user != self.request.user:
            raise RuntimeError

        if not user:
            self.request.db.add(
                UserIdentity(
                    user=self.request.user,
                    provider=IdentityProvider.GOOGLE,
                    provider_unique_id=google_id,
                )
            )

        self.request.session.flash("Google account connected ✓", "success")
        return HTTPFound(self.request.route_url("account"))

    def log_in_with_google(self, google_id: str, user):
        if not user:
            return HTTPFound(
                self.request.route_url(
                    "oidc.signup.google",
                    _query={
                        "auth": jwt.encode(
                            {"google_id": google_id},
                            "secret_key",
                            algorithm="HS256",
                        )
                    },
                )
            )

        return HTTPFound(
            self.request.route_url("activity.user_search", username=user.username),
            headers=login(user, self.request),
        )
