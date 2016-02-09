# -*- coding: utf-8 -*-

from h import features
from h.accounts import models as accounts_models
from h.api import models as api_models
from h.api.nipsa import models as nipsa_models
from h.groups import models as groups_models
from h.notification import models as notification_models
from h.badge import models as badge_models

__all__ = (
    'Activation',
    'Annotation',
    'Blocklist',
    'Document',
    'Feature',
    'Group',
    'NipsaUser',
    'Subscriptions',
    'User',
)


Activation = accounts_models.Activation
Annotation = api_models.Annotation
Blocklist = badge_models.Blocklist
Document = api_models.Document
Feature = features.Feature
Group = groups_models.Group
NipsaUser = nipsa_models.NipsaUser
Subscriptions = notification_models.Subscriptions
User = accounts_models.User


def includeme(_):
    # This module is included for side-effects only. SQLAlchemy models register
    # with the global metadata object when imported.
    pass
