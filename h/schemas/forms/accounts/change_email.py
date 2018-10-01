# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import colander
import deform

from h import i18n
from h.schemas import validators
from h.schemas.base import CSRFSchema
from h.schemas.forms.accounts.validators import unique_email
from h.models.user import (
    EMAIL_MAX_LENGTH
)

_ = i18n.TranslationString


def _validate_unique_email(*args):
    unique_email(*args)


class ChangeEmailSchema(CSRFSchema):

    email = colander.SchemaNode(
        colander.String(),
        validator=colander.All(
            validators.Length(max=EMAIL_MAX_LENGTH),
            validators.Email(),
            _validate_unique_email,
        ),
        title=_('Email address'),
        widget=deform.widget.TextInputWidget(template='emailinput'),
    )

    # No node-level validators
    # validation is on email field and on the form itself
    password = colander.SchemaNode(
        colander.String(),
        title=_('Confirm password'),
        widget=deform.widget.PasswordWidget(),
        hide_until_form_active=True,
    )

    def validator(self, node, value):
        super(ChangeEmailSchema, self).validator(node, value)
        exc = colander.Invalid(node)
        request = node.bindings['request']
        svc = request.find_service(name='user_password')
        user = request.user

        if not svc.check_password(user, value.get('password')):
            exc['password'] = _('Wrong password.')

        if exc.children:
            raise exc
