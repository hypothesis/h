# These will become private soon
from h.auth.policy._basic_http_auth import AuthClientPolicy
from h.auth.policy._cookie import CookieAuthenticationPolicy
from h.auth.policy._remote_user import RemoteUserAuthenticationPolicy
from h.auth.policy.bearer_token import TokenAuthenticationPolicy
from h.auth.policy.combined import APIAuthenticationPolicy, AuthenticationPolicy
