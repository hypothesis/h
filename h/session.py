from datetime import timedelta
from urllib.parse import urlparse

from pyramid.csrf import SessionCSRFStoragePolicy
from pyramid.session import JSONSerializer, SignedCookieSessionFactory

from h.security import derive_key
from h.security.policy.top_level import HTML_AUTHCOOKIE_MAX_AGE
from h.util.edu_domains import is_edu_email


def model(request):
    session = {}
    session["userid"] = request.authenticated_userid
    session["groups"] = _current_groups(request, request.default_authority)
    session["features"] = request.feature.all()
    # `_user_preferences` and not `_preferences`: this model is published to
    # *other* users. `h.services.group_members._publish` and
    # `group_create.create_private_group` build it from the acting user's
    # request and hand it to the streamer keyed by the target's userid, so
    # h/streamer/messages.py delivers one user's preferences to another's
    # sidebar, which applies them as its own. That is a pre-existing bug -- it
    # already misdelivers show_sidebar_tutorial -- but the EDU survey is the
    # first preference that decides something about who the user *is*, so it
    # stays out of the one path that crosses users. The survey reaches its own
    # user through `profile()`, which every client fetches on launch.
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
            "preferences": _preferences(request),
        },
        **user_info(user),
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


def _preferences(request):
    """
    Return the `preferences` object for the current user, for `profile()`.

    Split in two on purpose: `_user_preferences` answers what the user's own
    columns say, and anything that also depends on the request — a feature
    flag, the first-party authority — is decided here, so the older preferences
    keep being a plain read of the user.

    Only `profile()` uses this. `model()` deliberately stays on
    `_user_preferences`; the comment there says why.
    """
    preferences = _user_preferences(request.user)

    if show_edu_role_survey(request):
        preferences["show_instructor_survey"] = True

    return preferences


def _user_preferences(user):
    preferences = {}
    if user and not user.sidebar_tutorial_dismissed:
        preferences["show_sidebar_tutorial"] = True
    if user and not user.youtube_gdpr_banner_dismissed:
        preferences["show_youtube_gdpr_banner"] = True
    if user and user.shortcuts_preferences is not None:
        preferences["shortcuts_preferences"] = user.shortcuts_preferences
    return preferences


def can_answer_edu_role_survey(request):
    """
    Return True if the request's user is in the EDU role survey's audience.

    That is everything deciding who the survey is for -- the kill switch, the
    first-party authority, an educational email address -- but not whether they
    have answered it already; `show_edu_role_survey` adds that.

    The two questions are split because the write path needs this one on its
    own. `h.views.api.profile` rejects an answer from anyone outside the
    audience, but someone inside it who has already answered isn't writing
    where they were never asked -- they are sending a stale duplicate, which is
    dropped rather than rejected. One rule each, so a change to who gets the
    survey -- the PRD's plan to re-ask the people who dismissed it, say --
    moves both paths at once, with no second rule to keep in step.

    Note `request.default_authority` below, and not the local `authority` in
    `profile()`: that one holds the *user's* authority, so comparing against it
    would compare a value with itself and silently let every third-party user
    through.
    """
    # The `instructor_survey` flag is both the rollout control and the kill
    # switch. Checking it here rather than leaving it to the client means
    # turning it off stops the survey from the next profile fetch on, with no
    # new client bundle to propagate through the CDN and the browser extension.
    #
    # Two things it is not. It isn't instant: sidebars that are already open
    # keep the profile they were handed until they reload or the streamer sends
    # them a new one. And it isn't absolute: `FeatureService._state` honours the
    # `?__feature__[instructor_survey]` query param ahead of everything else, on
    # any request and for any user, so that override turns the survey back on
    # for whoever passes it -- on the write path as well as this one.
    if not request.feature("instructor_survey"):
        return False

    user = request.user

    if not user:
        return False

    # Restrict the survey to the first-party authority. The flag is configured
    # as first-party only, but that is not enough on its own: FeatureService
    # checks a flag's `everyone` column *before* it looks at the user's
    # authority and returns True without reading it, so widening a rollout with
    # that checkbox would reach every third-party authority too. Keeping the
    # check here makes the exclusion structural rather than a checkbox away.
    if user.authority != request.default_authority:
        return False

    return is_edu_email(user.email)


def show_edu_role_survey(request):
    """
    Return True if the request's user should be shown the EDU role survey.

    The survey is for web app users at educational institutions only, and is
    only ever shown until they answer it.
    """
    if not can_answer_edu_role_survey(request):
        return False

    # Any recorded answer stops us asking again, including a dismissal, so this
    # must test for NULL and not for falsiness: "not_instructor" and "dismissed"
    # are answers.
    return request.user.edu_role_survey_response is None


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
