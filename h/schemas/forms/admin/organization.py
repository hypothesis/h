from __future__ import unicode_literals

import colander
from deform.widget import TextAreaWidget, TextInputWidget

import h.i18n
from h import validators
from h.models.organization import Organization, ORGANIZATION_NAME_MIN_CHARS, ORGANIZATION_NAME_MAX_CHARS
from h.schemas.base import CSRFSchema

_ = h.i18n.TranslationString


def validate_logo(node, value):
    try:
        Organization(logo=value)
    except Exception:
        raise colander.Invalid(node, _('Logo is not valid SVG'))


class OrganizationSchema(CSRFSchema):

    authority = colander.SchemaNode(
        colander.String(),
        title=_('Authority'),
    )

    name = colander.SchemaNode(
        colander.String(),
        title=_('Name'),
        validator=validators.Length(ORGANIZATION_NAME_MIN_CHARS, ORGANIZATION_NAME_MAX_CHARS),
        widget=TextInputWidget(max_length=ORGANIZATION_NAME_MAX_CHARS),
    )

    logo = colander.SchemaNode(
        colander.String(),
        title=_('Logo'),
        hint=_('SVG markup for logo. You can get this from a .svg file by'
               ' opening it in a text editor and copying the contents.'),
        widget=TextAreaWidget(rows=5),
        validator=validate_logo,
        missing=None,
    )
