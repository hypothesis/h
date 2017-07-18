# -*- coding: utf-8 -*-

"""Factory classes for easily generating test objects."""

from .base import set_session

from .activation import Activation
from .annotation import Annotation
from .annotation_moderation import AnnotationModeration
from .auth_client import AuthClient
from .auth_ticket import AuthTicket
from .authz_code import AuthzCode
from .document import Document, DocumentMeta, DocumentURI
from .feature import Feature
from .feature_cohort import FeatureCohort
from .flag import Flag
from .group import Group, PublisherGroup
from .setting import Setting
from .token import Token
from .user import User

__all__ = (
    'Activation',
    'Annotation',
    'AnnotationModeration',
    'AuthClient',
    'AuthTicket',
    'AuthzCode',
    'Document',
    'DocumentMeta',
    'DocumentURI',
    'Feature',
    'FeatureCohort',
    'Flag',
    'Group',
    'PublisherGroup',
    'Setting',
    'Token',
    'User',
    'set_session',
)
