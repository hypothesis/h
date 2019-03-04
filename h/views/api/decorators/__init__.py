# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from h.views.api.decorators.client_errors import (
    unauthorized_to_not_found,
    not_found_reason,
)

__all__ = ("unauthorized_to_not_found", "not_found_reason")
