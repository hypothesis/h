# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import colander
from deform.widget import SelectWidget

from h import i18n
from h import validators
from h.models.group import (
    GROUP_NAME_MIN_LENGTH,
    GROUP_NAME_MAX_LENGTH,
)
from h.schemas.base import CSRFSchema

_ = i18n.TranslationString

VALID_GROUP_TYPES = (
    (u'private', _('Private')),
    (u'restricted', _('Restricted')),
    (u'open', _('Open')),
)


class CreateAdminGroupSchema(CSRFSchema):

    group_type = colander.SchemaNode(
        colander.String(),
        title=_('Group Type'),
        widget=SelectWidget(values=((u'', _('Select')),) + VALID_GROUP_TYPES)
    )

    name = colander.SchemaNode(
        colander.String(),
        title=_('Group Name'),
        validator=validators.Length(min=GROUP_NAME_MIN_LENGTH,
                                    max=GROUP_NAME_MAX_LENGTH),
    )

    authority = colander.SchemaNode(
        colander.String(),
        title=_('Authority'),
        description=_("The group's authority"),
        hint=_('The authority within which this group should be created.'
               ' Note that only users within the designated authority'
               ' will be able to be associated with this group (as'
               ' creator or member).')
    )

    creator = colander.SchemaNode(
        colander.String(),
        title=_('Creator'),
        description=_("Username for this group's creator"),
        hint=_('This user will be set as the "creator" of the group. Note that'
               ' the user must be on the same authority as the group authority'),
    )
