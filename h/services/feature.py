import re

from packaging import version

from h import models
from h.models import User
from h.util.db import lru_cache_in_transaction

PARAM_PATTERN = re.compile(r"\A__feature__\[(?P<featurename>[A-Za-z0-9_-]+)\]\Z")


class UnknownFeatureError(Exception):
    pass


class FeatureRequestProperty:
    """
    Helper object for accessing feature flags.

    An instance of FeatureRequestProperty is available on the request object
    as ``request.feature`` in order to simplify access to the feature service.
    """

    def __init__(self, request):
        self.request = request
        self.svc = request.find_service(name="feature")

    def __call__(self, name):
        """Get the status of feature flag `name` for the current user."""
        return self.svc.enabled(name, user=self.request.user)

    def all(self):
        """Get the status of all feature flags for the current user."""
        return self.svc.all(user=self.request.user)


class FeatureService:
    """
    Manages access to feature flag status.

    This service manages the retrieval of feature flag data from the database
    and answers queries about the status of feature flags for particular
    users.

    :param session: the database session
    :type session: sqlalchemy.orm.session.Session
    :param overrides: map of feature flag name to on/off state. This overrides
        the state based on the user's identity.
    """

    overrides: dict[str, bool] | None

    def __init__(
        self,
        session,
        overrides: dict[str, bool] | None = None,
        default_authority=None,
        *,
        facebook_enabled_by_query_param=False,
    ):
        self.default_authority = default_authority
        self.session = session
        self.overrides = overrides
        self.facebook_enabled_by_query_param = facebook_enabled_by_query_param

        self._cached_load = lru_cache_in_transaction(self.session)(self._load)

    def enabled(self, name: str, user: User | None) -> bool:
        """
        Determine if the named feature is enabled for the specified `user`.

        If the feature has no override in the database, it will default to
        False. Features must be documented, and an UnknownFeatureError will be
        thrown if an undocumented feature is interrogated.
        """
        features = self.all(user=user)

        if name not in features:
            raise UnknownFeatureError(f"{name} is not a valid feature name")  # noqa: EM102, TRY003

        return features[name]

    def all(self, user=None):
        """Return a dict mapping feature flag names to enabled states for the specified `user`."""
        return {f.name: self._state(f, user=user) for f in self._cached_load()}

    def _load(self):
        """Load the feature flags from the database."""
        return models.Feature.all(self.session)

    def _state(self, feature, user=None):  # noqa: PLR0911
        # This is a temporary hack to allow log-in-with-Facebook to be tested
        # on production without exposing all users to it.  This should be
        # removed after log-in-with-Facebook has been released.
        if (
            feature.name == "log_in_with_facebook"
            and self.facebook_enabled_by_query_param
        ):  # pragma: no cover
            return True

        # Handle explicit overrides
        if self.overrides is not None and feature.name in self.overrides:
            return self.overrides[feature.name]

        # Features that are on for everyone are on.
        if feature.everyone:
            return True
        if user is not None:
            if feature.first_party and user.authority == self.default_authority:
                return True
            # Features that are on for admin are on if the user is an admin.
            if feature.admins and user.admin:
                return True
            # Features that are on for staff are on if the user is a staff member.
            if feature.staff and user.staff:
                return True
            # If the feature is in a cohort that the user is a member of, the
            # feature is on.
            if set(feature.cohorts) & set(user.cohorts):
                return True
        return False


def feature_service_factory(_context, request):
    return FeatureService(
        session=request.db,
        overrides=_feature_overrides(request),
        default_authority=request.default_authority,
        facebook_enabled_by_query_param="facebook" in request.GET,
    )


MIN_CLIENT_VERSION = {"pdf_image_annotation": "1.1633.0"}
"""
Minimum client versions for certain feature flags.

This can be used to disable feature flags in older clients which understand a
flag, but have incomplete implementations.
"""


def _feature_overrides(request) -> dict[str, bool]:
    """
    Get the list of overridden features for the specified request.

    If "__feature__[<featurename>]" is in the query string, then the feature
    is overridden to on. This allows testing feature flags for logged-out
    users.
    """
    overrides = {}

    # Handle manual overrides via query params.
    for param in request.GET:
        match = PARAM_PATTERN.match(param)
        if match:
            name = match.group("featurename")
            overrides[name] = True

    # Disable certain features in older clients.
    client_version = None
    try:
        if header := request.headers.get("Hypothesis-Client-Version"):
            client_version = version.parse(header)
    except version.InvalidVersion:
        pass
    if client_version:
        for feature_name, min_version in MIN_CLIENT_VERSION.items():
            if client_version < version.parse(min_version):
                overrides[feature_name] = False

    return overrides
