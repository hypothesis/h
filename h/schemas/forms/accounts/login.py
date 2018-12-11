# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import colander
import deform

from h import i18n
from h.services.user import UserNotActivated
from h.schemas.base import CSRFSchema

_ = i18n.TranslationString


class LoginSchema(CSRFSchema):
    username = colander.SchemaNode(
        colander.String(),
        title=_("Username / email"),
        widget=deform.widget.TextInputWidget(autofocus=True),
    )
    password = colander.SchemaNode(
        colander.String(), title=_("Password"), widget=deform.widget.PasswordWidget()
    )

    def validator(self, node, value):
        super(LoginSchema, self).validator(node, value)

        request = node.bindings["request"]
        username = value.get("username")
        password = value.get("password")

        user_service = request.find_service(name="user")
        user_password_service = request.find_service(name="user_password")

        try:
            user = user_service.fetch_for_login(username_or_email=username)
        except UserNotActivated:
            err = colander.Invalid(node)
            err["username"] = _(
                "Please check your email and open the link " "to activate your account."
            )
            raise err

        if user is None:
            err = colander.Invalid(node)
            err["username"] = _("User does not exist.")
            raise err

        if not user_password_service.check_password(user, password):
            err = colander.Invalid(node)
            err["password"] = _("Wrong password.")
            raise err

        value["user"] = user
