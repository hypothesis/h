# -*- coding: utf-8 -*-
"""
A module into which all ORM classes are imported.

To avoid circular imports almost all code should import ORM classes from this
module rather than importing them directly,
``from h import models`` rather than ``from h.foo import models``

This is a convenience - you can just import this one module and all of the
ORM classes will be defined, instead of having to import every models module
individually.

For example when testing ORM classes the test module for ``h.foo.models.Bar``
can't just import ``h.foo.models``, it would also need to import the models
module for each database table that ``Bar`` has a (direct or indirect) foreign
key to. So for convenience the test module can instead just do
``from h import models`` and have all ORM classes be defined.

"""

from memex.models.annotation import Annotation
from memex.models.document import Document, DocumentMeta, DocumentURI
from h.features import models as features_models
from h.groups import models as groups_models
from h.nipsa import models as nipsa_models
from h.notification import models as notification_models
from h.badge import models as badge_models
from h.followers import models as follower_models
from h.managers import models as manager_models

from h.models.activation import Activation
from h.models.auth_client import AuthClient
from h.models.token import Token
from h.models.user import User

__all__ = (
    'Activation',
    'Annotation',
    'AuthClient',
    'Blocklist',
    'Document',
    'DocumentMeta',
    'DocumentURI',
    'Feature',
    'Group',
    'NipsaUser',
    'Subscriptions',
    'Token',
    'User',
    'Follower',
    'Manager'
)


Blocklist = badge_models.Blocklist
Feature = features_models.Feature
FeatureCohort = features_models.FeatureCohort
Group = groups_models.Group
NipsaUser = nipsa_models.NipsaUser
Subscriptions = notification_models.Subscriptions
Follower = follower_models.Follower
Manager = manager_models.Manager


def includeme(_):
    # This module is included for side-effects only. SQLAlchemy models register
    # with the global metadata object when imported.
    pass
