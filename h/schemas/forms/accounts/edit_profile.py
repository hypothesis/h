# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import colander
import deform

from h import i18n
from h.accounts import util
from h.models.user import DISPLAY_NAME_MAX_LENGTH
from h.schemas import validators
from h.schemas.base import CSRFSchema

_ = i18n.TranslationString


def validate_url(node, cstruct):
    try:
        util.validate_url(cstruct)
    except ValueError as exc:
        raise colander.Invalid(node, str(exc))


def validate_orcid(node, cstruct):
    try:
        util.validate_orcid(cstruct)
    except ValueError as exc:
        raise colander.Invalid(node, str(exc))


class EditProfileSchema(CSRFSchema):
    display_name = colander.SchemaNode(
        colander.String(),
        missing=None,
        validator=validators.Length(max=DISPLAY_NAME_MAX_LENGTH),
        title=_("Display name"),
    )

    description = colander.SchemaNode(
        colander.String(),
        missing=None,
        validator=validators.Length(max=250),
        widget=deform.widget.TextAreaWidget(max_length=250, rows=4),
        title=_("Description"),
    )

    location = colander.SchemaNode(
        colander.String(),
        missing=None,
        validator=validators.Length(max=100),
        title=_("Location"),
    )

    link = colander.SchemaNode(
        colander.String(),
        missing=None,
        validator=colander.All(validators.Length(max=250), validate_url),
        title=_("Link"),
    )

    orcid = colander.SchemaNode(
        colander.String(),
        missing=None,
        validator=validate_orcid,
        title=_("ORCID"),
        hint=_(
            "ORCID provides a persistent identifier for researchers (see orcid.org)."
        ),
    )
