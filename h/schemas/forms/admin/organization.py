from __future__ import unicode_literals

import colander
from deform.widget import TextAreaWidget, TextInputWidget
from xml.etree import ElementTree

import h.i18n
from h.models.organization import (
    ORGANIZATION_NAME_MIN_CHARS,
    ORGANIZATION_NAME_MAX_CHARS,
)
from h.schemas import validators
from h.schemas.base import CSRFSchema

_ = h.i18n.TranslationString


ORGANIZATION_LOGO_MAX_CHARS = 100000


def _strip_xmlns(tag):
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def validate_logo(node, value):
    if len(value) > ORGANIZATION_LOGO_MAX_CHARS:
        raise colander.Invalid(
            node,
            _(
                "Logo is larger than {:,d} characters".format(
                    ORGANIZATION_LOGO_MAX_CHARS
                )
            ),
        )
    try:
        root = ElementTree.fromstring(value)
    except ElementTree.ParseError:
        raise colander.Invalid(node, _("Logo is not parsable XML"))

    if _strip_xmlns(root.tag) != "svg":
        raise colander.Invalid(node, _("Logo does not start with <svg> tag"))


class OrganizationSchema(CSRFSchema):

    authority = colander.SchemaNode(colander.String(), title=_("Authority"))

    name = colander.SchemaNode(
        colander.String(),
        title=_("Name"),
        validator=validators.Length(
            ORGANIZATION_NAME_MIN_CHARS, ORGANIZATION_NAME_MAX_CHARS
        ),
        widget=TextInputWidget(max_length=ORGANIZATION_NAME_MAX_CHARS),
    )

    logo = colander.SchemaNode(
        colander.String(),
        title=_("Logo"),
        hint=_(
            "SVG markup for logo. You can get this from a .svg file by"
            " opening it in a text editor and copying the contents."
        ),
        widget=TextAreaWidget(rows=5),
        validator=validate_logo,
        missing=None,
    )
