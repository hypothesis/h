# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import colander
import deform

from h.schemas import validators


PASSWORD_MIN_LENGTH = 2  # FIXME: this is ridiculous


def new_password_node(**kwargs):
    """Return a Colander schema node for a new user password."""
    kwargs.setdefault("widget", deform.widget.PasswordWidget())
    return colander.SchemaNode(
        colander.String(),
        validator=validators.Length(min=PASSWORD_MIN_LENGTH),
        **kwargs
    )
