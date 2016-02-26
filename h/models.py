# -*- coding: utf-8 -*-

from h import features
from h.accounts import models as accounts_models
from h.auth import models as auth_models
from h.api.models.annotation import Annotation
from h.api.models.document import Document, DocumentMeta, DocumentURI
from h.groups import models as groups_models
from h.nipsa import models as nipsa_models
from h.notification import models as notification_models
from h.badge import models as badge_models

__all__ = (
    'Activation',
    'Annotation',
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
)


Activation = accounts_models.Activation
Blocklist = badge_models.Blocklist
Feature = features.Feature
Group = groups_models.Group
NipsaUser = nipsa_models.NipsaUser
Token = auth_models.Token
Subscriptions = notification_models.Subscriptions
User = accounts_models.User


def includeme(_):
    # This module is included for side-effects only. SQLAlchemy models register
    # with the global metadata object when imported.
    pass
