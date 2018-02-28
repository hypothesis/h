# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import colander

from h import i18n
from h import validators
from h.models.group import (
    GROUP_NAME_MIN_LENGTH,
    GROUP_NAME_MAX_LENGTH,
)
from h.schemas.base import CSRFSchema

_ = i18n.TranslationString


class CreateAdminGroupSchema(CSRFSchema):
    name = colander.SchemaNode(
        colander.String(),
        title=_('Name'),
        validator=validators.Length(min=GROUP_NAME_MIN_LENGTH,
                                    max=GROUP_NAME_MAX_LENGTH),
    )

    authority = colander.SchemaNode(
        colander.String(),
        title=_('Authority'),
        hint=_('The authority within which this group should be created.'
               ' Note that only users within the designated authority'
               ' will be able to be associated with this group (as'
               ' creator or member).')
    )
