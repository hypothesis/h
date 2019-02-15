# -*- coding: utf-8 -*-
from __future__ import unicode_literals

API_VERSIONS = ["v1"]
API_VERSION_DEFAULT = "v1"

__all__ = ("API_VERSIONS", "API_VERSION_DEFAULT")


def includeme(config):
    config.scan(__name__)
