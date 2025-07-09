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
class FacebookConnectAndLoginViews:
    def __init__(self, request) -> None:
        self.request = request

    @view_config(is_authenticated=True, route_name="oidc.connect.facebook")
    @view_config(is_authenticated=False, route_name="oidc.login.facebook")
    def connect_or_login(self):
        client_id = environ["FACEBOOK_OIDC_CLIENT_ID"]
        state_signing_key = environ["FACEBOOK_OIDC_STATE_SIGNING_KEY"]

        actions = {"oidc.connect.facebook": "connect", "oidc.login.facebook": "login"}
        action = actions[self.request.matched_route.name]

        state = jwt.encode(
            {"action": action, "rfp": secrets.token_hex()},
            state_signing_key,
            algorithm="HS256",
        )
        self.request.session["oidc.state.facebook"] = state
        return HTTPFound(
            location=urlunparse(
                (
                    "https",
                    "www.facebook.com",
                    "/v11.0/dialog/oauth",
                    "",
                    urlencode(
                        {
                            "client_id": client_id,
                            "response_type": "code",
                            "redirect_uri": self.request.route_url(
                                "oidc.redirect.facebook"
                            ),
                            "state": state,
                            "scope": "openid email",
                        }
                    ),
                    "",
                )
            )
        )


@view_defaults(request_method="GET", route_name="oidc.redirect.facebook")
class FacebookRedirectViews:
    def __init__(self, request) -> None:
        self.request = request
        self.openid_client = request.find_service(OpenIDClientService)
        self.user_service = request.find_service(name="user")

    @view_config()
    def redirect(self):
        state_signing_key = environ["FACEBOOK_OIDC_STATE_SIGNING_KEY"]

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
            "https://graph.facebook.com/v11.0/oauth/access_token",
            params={
                "client_id": environ["FACEBOOK_OIDC_CLIENT_ID"],
                "client_secret": environ["FACEBOOK_OIDC_CLIENT_SECRET"],
                "redirect_uri": self.request.route_url("oidc.redirect.facebook"),
                "code": self.request.params["code"],
            },
        )

        id_token = token_url_response.json()["id_token"]

        decoded_id_token = JWTService.decode_token(
            id_token,
            "https://limited.facebook.com/.well-known/oauth/openid/jwks/",
            ["RS256"],
        )

        facebook_id = decoded_id_token["sub"]
        breakpoint()

        user = self.user_service.fetch_by_identity(
            IdentityProvider.FACEBOOK, facebook_id
        )

        actions = {
            "connect": functools.partial(self.connect_facebook_id, facebook_id, user),
            "login": functools.partial(self.log_in_with_facebook, facebook_id, user),
        }
        action_method = actions[action_str]
        return action_method()

    def connect_facebook_id(self, facebook_id: str, user):
        if user and user != self.request.user:
            raise RuntimeError

        if not user:
            self.request.db.add(
                UserIdentity(
                    user=self.request.user,
                    provider=IdentityProvider.FACEBOOK,
                    provider_unique_id=facebook_id,
                )
            )

        self.request.session.flash("Facebook account connected ✓", "success")
        return HTTPFound(self.request.route_url("account"))

    def log_in_with_facebook(self, facebook_id: str, user):
        if not user:
            return HTTPFound(
                self.request.route_url(
                    "oidc.signup.facebook",
                    _query={
                        "auth": jwt.encode(
                            {"facebook_id": facebook_id},
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
