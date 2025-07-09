import datetime

import jwt
from pyramid.csrf import get_csrf_token
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config, view_defaults

from h.views.helpers import login


@view_defaults(
    route_name="oidc.signup.orcid",
    is_authenticated=False,
    renderer="h:templates/oidc_signup.html.jinja2",
)
class OIDCSignupController:
    def __init__(self, request):
        self.request = request

    @view_config(request_method="GET")
    def get(self):
        return {"js_config": self.js_config}

    @view_config(request_method="POST")
    def post(self):
        orcid_id = self.auth["orcid_id"]
        signup_service = self.request.find_service(name="user_signup")

        # Create a new Hypothesis account connected to the user's ORCID iD.
        user = signup_service.signup(
            username=self.request.params["username"],
            email=self.request.params["email"],
            password=None,
            privacy_accepted=datetime.datetime.now(datetime.UTC),
            comms_opt_in=self.request.params.get("comms_opt_in", None) == "yes",
            # Pre-activate the account. In the real implementation we would
            # only do this if request.params["email"] is a pre-verified email
            # that we received from ORCID.
            require_activation=False,
            # Create a UserIdentity for the user's ORCID iD and connect it to
            # the new account we're creating.
            identities=[{"provider": "orcid.org", "provider_unique_id": orcid_id}],
        )

        # Log the user into their shiny new Hypothesis account and redirect
        # them to their user profile page.
        return HTTPFound(
            self.request.route_url("activity.user_search", username=user.username),
            headers=login(user, self.request),
        )

    @property
    def auth(self):
        auth_jwt = self.request.params["auth"]
        # For good measure, in the real implementation we should also bind this
        # JWT to the session cookie and refuse to decode it outside of the
        # matching session.
        decoded_auth_jwt = jwt.decode(auth_jwt, "secret_key", algorithms=["HS256"])
        return decoded_auth_jwt

    @property
    def js_config(self):
        orcid_id = self.auth["orcid_id"]
        return {
            "csrfToken": get_csrf_token(self.request),
            "oidc": {"orcidId": orcid_id},
        }
