# -*- coding: utf-8 -*-

import colander

from h.accounts.schemas import CSRFSchema
from h.groups.models import GROUP_NAME_MIN_LENGTH
from h.groups.models import GROUP_NAME_MAX_LENGTH


class GroupSchema(CSRFSchema):

    """The schema for the create-a-new-group form."""

    name = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(
            min=GROUP_NAME_MIN_LENGTH,
            max=GROUP_NAME_MAX_LENGTH))
