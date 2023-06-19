import re

from h import models
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
    :param overrides: the names of any overridden flags
    :type overrides: list
    """

    def __init__(self, session, overrides=None, default_authority=None):
        self.default_authority = default_authority
        self.session = session
        self.overrides = overrides

        self._cached_load = lru_cache_in_transaction(self.session)(self._load)

    def enabled(self, name, user=None):
        """
        Determine if the named feature is enabled for the specified `user`.

        If the feature has no override in the database, it will default to
        False. Features must be documented, and an UnknownFeatureError will be
        thrown if an undocumented feature is interrogated.
        """
        features = self.all(user=user)

        if name not in features:
            raise UnknownFeatureError(f"{name} is not a valid feature name")

        return features[name]

    def all(self, user=None):
        """Return a dict mapping feature flag names to enabled states for the specified `user`."""
        return {f.name: self._state(f, user=user) for f in self._cached_load()}

    def _load(self):
        """Load the feature flags from the database."""
        return models.Feature.all(self.session)

    def _state(self, feature, user=None):  # pylint:disable=too-many-return-statements
        # Features that are explicitly overridden are on.
        if self.overrides is not None and feature.name in self.overrides:
            return True
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
    )


def _feature_overrides(request):
    """
    Get the list of manually-overridden features for the specified request.

    If "__feature__[<featurename>]" is in the query string, then the feature
    is overridden to on. This allows testing feature flags for logged-out
    users.
    """
    overrides = []
    for param in request.GET:
        match = PARAM_PATTERN.match(param)
        if match:
            overrides.append(match.group("featurename"))
    return overrides
