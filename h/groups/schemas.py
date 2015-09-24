# -*- coding: utf-8 -*-

import colander

from h.accounts.schemas import CSRFSchema


class GroupSchema(CSRFSchema):

    """The schema for the create-a-new-group form."""

    name = colander.SchemaNode(colander.String(),
                               validator=colander.Length(min=4, max=25))
