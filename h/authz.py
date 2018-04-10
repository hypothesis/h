# -*- coding: utf-8 -*-

"""Authorization configuration."""
from __future__ import unicode_literals

from pyramid.authorization import ACLAuthorizationPolicy

__all__ = ()


def includeme(config):
    config.set_authorization_policy(ACLAuthorizationPolicy())
