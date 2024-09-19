from datetime import timedelta
from urllib.parse import urlparse

from pyramid.csrf import SessionCSRFStoragePolicy
from pyramid.session import JSONSerializer, SignedCookieSessionFactory

from h.security import derive_key
from h.security.policy.top_level import HTML_AUTHCOOKIE_MAX_AGE


def model(request):
    session = {}
    session["userid"] = request.authenticated_userid
    session["groups"] = _current_groups(request, request.default_authority)
    session["features"] = request.feature.all()
    session["preferences"] = _user_preferences(request.user)
    return session


def profile(request, authority=None):
    """
    Return a representation of the current user's information and settings.

    If the request is unauthenticated (and so not tied to a particular
    authority), the authority parameter can be used to override the authority
    used to find public groups (by default, this is the `authority` of the
    request). This parameter is ignored for authenticated requests.

    """
    user = request.user

    if user is not None:
        authority = user.authority
    else:
        authority = authority or request.default_authority

    return dict(
        {
            "userid": request.authenticated_userid,
            "authority": authority,
            "groups": _current_groups(request, authority),
            "features": request.feature.all(),
            "preferences": _user_preferences(user),
        },
        **user_info(user)
    )


def user_info(user):
    """
    Return the `user_info` JSON object.

    This is being used in the JSON representation of an annotation,
    and for the user profile.
    """
    if user is None:
        return {}

    return {"user_info": {"display_name": user.display_name}}


def pop_flash(request):  # pragma: no cover
    return {
        k: request.session.pop_flash(k) for k in ["error", "info", "warning", "success"]
    }


def _current_groups(request, authority):
    """
    Return a list of the groups the current user is a member of.

    This list is meant to be returned to the client in the "session" model.
    """

    user = request.user
    svc = request.find_service(name="group_list")
    groups = svc.session_groups(user=user, authority=authority)

    return [_group_model(request.route_url, group) for group in groups]


def _group_model(route_url, group):
    model_ = {"name": group.name, "id": group.pubid, "public": group.is_public}

    # We currently want to show URLs for secret groups, but not for open
    # groups, and not for the `__world__` group (where it doesn't make sense).
    # This is currently all non-public groups, which saves us needing to do a
    # check in here on the group's authority.
    if not group.is_public:
        model_["url"] = route_url("group_read", pubid=group.pubid, slug=group.slug)
    return model_


def _user_preferences(user):
    preferences = {}
    if user and not user.sidebar_tutorial_dismissed:
        preferences["show_sidebar_tutorial"] = True
    return preferences


def includeme(config):  # pragma: no cover
    settings = config.registry.settings
    secure = urlparse(settings.get("h.app_url")).scheme == "https"

    # By default, derive_key generates a 64-byte (512 bit) secret, which is the
    # correct length for SHA512-based HMAC as specified by the `hashalg`.
    factory = SignedCookieSessionFactory(
        secret=derive_key(
            settings["secret_key"], settings["secret_salt"], b"h.session.cookie_secret"
        ),
        hashalg="sha512",
        httponly=True,
        secure=secure,
        serializer=JSONSerializer(),
        # One thing h uses the session for is to store CSRF tokens (see
        # SessionCSRFStoragePolicy() below).
        #
        # The auth cookies that keep users logged in to h web pages have a
        # lifetime of HTML_AUTHCOOKIE_MAX_AGE so in theory a user can leave a
        # tab open (say a page containing a form) for up to
        # HTML_AUTHCOOKIE_MAX_AGE and then return to the tab and expect to be
        # able to submit the form.
        #
        # However, even if the user's auth cookie is still valid their form
        # submission will still fail if the form's CSRF token has expired and
        # the user will see a BadCSRFToken error.
        #
        # To avoid this we make sure that the lifetime of CSRF tokens is always
        # longer than the lifetimes of auth cookies.
        timeout=HTML_AUTHCOOKIE_MAX_AGE + int(timedelta(hours=1).total_seconds()),
    )
    config.set_session_factory(factory)
    config.set_csrf_storage_policy(SessionCSRFStoragePolicy())
