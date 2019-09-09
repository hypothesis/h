# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from pyramid.csrf import SessionCSRFStoragePolicy
from pyramid.session import SignedCookieSessionFactory, JSONSerializer

from h.security import derive_key


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

    profile = {}
    profile["userid"] = request.authenticated_userid
    profile["authority"] = authority
    profile["groups"] = _current_groups(request, authority)
    profile["features"] = request.feature.all()
    profile["preferences"] = _user_preferences(user)

    profile.update(user_info(user))

    return profile


def user_info(user):
    """
    Returns the `user_info` JSON object.

    This is being used in the JSON representation of an annotation,
    and for the user profile.
    """
    if user is None:
        return {}

    return {"user_info": {"display_name": user.display_name}}


def pop_flash(request):
    return {
        k: request.session.pop_flash(k) for k in ["error", "info", "warning", "success"]
    }


def _current_groups(request, authority):
    """Return a list of the groups the current user is a member of.

    This list is meant to be returned to the client in the "session" model.

    """

    user = request.user
    svc = request.find_service(name="group_list")
    groups = svc.session_groups(user=user, authority=authority)

    return [_group_model(request.route_url, group) for group in groups]


def _group_model(route_url, group):
    model = {"name": group.name, "id": group.pubid, "public": group.is_public}

    # We currently want to show URLs for secret groups, but not for open
    # groups, and not for the `__world__` group (where it doesn't make sense).
    # This is currently all non-public groups, which saves us needing to do a
    # check in here on the group's authority.
    if not group.is_public:
        model["url"] = route_url("group_read", pubid=group.pubid, slug=group.slug)
    return model


def _user_preferences(user):
    preferences = {}
    if user and not user.sidebar_tutorial_dismissed:
        preferences["show_sidebar_tutorial"] = True
    return preferences


def includeme(config):
    settings = config.registry.settings

    # By default, derive_key generates a 64-byte (512 bit) secret, which is the
    # correct length for SHA512-based HMAC as specified by the `hashalg`.
    factory = SignedCookieSessionFactory(
        secret=derive_key(
            settings["secret_key"], settings["secret_salt"], b"h.session.cookie_secret"
        ),
        hashalg="sha512",
        httponly=True,
        timeout=3600,
        serializer=JSONSerializer(),
    )
    config.set_session_factory(factory)
    config.set_csrf_storage_policy(SessionCSRFStoragePolicy())
