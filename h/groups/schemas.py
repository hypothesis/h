# -*- coding: utf-8 -*-

import colander

from h.accounts.schemas import CSRFSchema


class GroupSchema(CSRFSchema):
    name = colander.SchemaNode(colander.String(),
                               validator=colander.Length(min=4, max=100))
