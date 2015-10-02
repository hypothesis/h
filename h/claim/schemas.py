# -*- coding: utf-8 -*-

from h import i18n
from h.accounts.schemas import CSRFSchema
from h.accounts.schemas import password_node


_ = i18n.TranslationString


class UpdateAccountSchema(CSRFSchema):
    password = password_node(title=_('New password'),
                             hint=_('at least two characters'))
