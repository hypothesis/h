# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import colander
from deform.widget import SelectWidget, SequenceWidget, TextAreaWidget, TextInputWidget

from h import i18n
from h import validators
from h.models.group import (
    GROUP_NAME_MIN_LENGTH,
    GROUP_NAME_MAX_LENGTH,
    GROUP_DESCRIPTION_MAX_LENGTH
)
from h.schemas.base import CSRFSchema

_ = i18n.TranslationString

VALID_GROUP_TYPES = (
    ('restricted', _('Restricted')),
    ('open', _('Open')),
)


def user_exists_validator_factory(user_svc):
    def user_exists_validator(form, value):
        user = user_svc.fetch(value['creator'], value['authority'])
        if user is None:
            exc = colander.Invalid(form, _('User not found'))
            exc['creator'] = 'User {creator} not found at authority {authority}'.format(
                creator=value['creator'],
                authority=value['authority']
            )
            raise exc
    return user_exists_validator


@colander.deferred
def group_type_validator(node, kw):
    group = kw.get('group')
    if not group:
        return colander.OneOf([key for key, title in VALID_GROUP_TYPES])

    def validate(node, value):
        if group.type != value:
            raise colander.Invalid(node, _('Changing group type is currently not supported'))
    return validate


class CreateAdminGroupSchema(CSRFSchema):

    group_type = colander.SchemaNode(
        colander.String(),
        title=_('Group Type'),
        widget=SelectWidget(
          values=(('', _('Select')),) + VALID_GROUP_TYPES
        ),
        validator=group_type_validator,
    )

    name = colander.SchemaNode(
        colander.String(),
        title=_('Group Name'),
        validator=validators.Length(min=GROUP_NAME_MIN_LENGTH,
                                    max=GROUP_NAME_MAX_LENGTH),
        widget=TextInputWidget(max_length=GROUP_NAME_MAX_LENGTH),
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

    description = colander.SchemaNode(
        colander.String(),
        title=_('Description'),
        description=_('Optional group description'),
        validator=colander.Length(max=GROUP_DESCRIPTION_MAX_LENGTH),
        widget=TextAreaWidget(rows=3, max_length=GROUP_DESCRIPTION_MAX_LENGTH),
        missing=None
    )

    origins = colander.SequenceSchema(
        colander.Sequence(),
        colander.SchemaNode(colander.String(),
                            name='origin',
                            validator=colander.url),
        title=_('Scope Origins'),
        hint=_('Origins where this group appears (e.g. "https://example.com")'),
        widget=SequenceWidget(add_subitem_text_template=_('Add origin'), min_len=1),
        validator=colander.Length(min=1, min_err=_('At least one origin must be specified'))
    )
