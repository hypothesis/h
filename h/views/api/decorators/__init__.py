# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from h.views.api.decorators.client_errors import (
    unauthorized_to_not_found,
    normalize_not_found,
    validate_media_types,
)
from h.views.api.decorators.response import version_media_type_header

__all__ = (
    "unauthorized_to_not_found",
    "normalize_not_found",
    "validate_media_types",
    "version_media_type_header",
)
