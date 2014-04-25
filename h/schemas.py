# -*- coding: utf-8 -*-
# pylint: disable=no-init, too-few-public-methods
import colander
import deform
from horus.schemas import ForgotPasswordSchema, unique_email
from pyramid.session import check_csrf_token

from h import interfaces
from h.models import _, get_session


@colander.deferred
def deferred_csrf_token(node, kw):
    request = kw.get('request')
    return request.session.get_csrf_token()


def unique_username(node, value):
    '''Colander validator that ensures the username does not exist.'''
    req = node.bindings['request']
    User = req.registry.getUtility(interfaces.IUserClass)
    if get_session(req).query(User).filter(User.username.ilike(value)).count():
        Str = req.registry.getUtility(interfaces.IUIStrings)
        raise colander.Invalid(node, Str.registration_username_exists)


class CSRFSchema(colander.Schema):
    """
    A CSRFSchema backward-compatible with the one from the hem module.

    Unlike hem, this doesn't require that the csrf_token appear in the
    serialized appstruct.
    """

    csrf_token = colander.SchemaNode(colander.String(),
                                     widget=deform.widget.HiddenWidget(),
                                     default=deferred_csrf_token,
                                     missing=None)

    def validator(self, form, value):  # pylint: disable=R0201
        request = form.bindings['request']
        check_csrf_token(request)


class LoginSchema(CSRFSchema):
    username = colander.SchemaNode(colander.String())
    password = colander.SchemaNode(
        colander.String(),
        widget=deform.widget.PasswordWidget()
    )


class RegisterSchema(CSRFSchema):
    username = colander.SchemaNode(
        colander.String(),
        validator=colander.All(
            colander.Length(min=3, max=15),
            colander.Regex('(?i)^[A-Z0-9._]+$'),
            unique_username,
        ),
    )
    email = colander.SchemaNode(
        colander.String(),
        validator=colander.All(
            colander.Email(),
            unique_email,
        ),
    )
    password = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(min=2),
        widget=deform.widget.PasswordWidget()
    )


class ResetPasswordSchema(CSRFSchema):
    username = colander.SchemaNode(
        colander.String(),
        widget=deform.widget.TextInputWidget(template='readonly/textinput'),
        missing=colander.null,
    )
    password = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(min=2),
        widget=deform.widget.PasswordWidget()
    )


class ActivateSchema(CSRFSchema):
    code = colander.SchemaNode(
        colander.String(),
        title="Security Code"
    )
    password = colander.SchemaNode(
        colander.String(),
        title=_('New Password'),
        validator=colander.Length(min=2),
        widget=deform.widget.PasswordWidget()
    )


def includeme(config):
    schemas = [
        (interfaces.ILoginSchema, LoginSchema),
        (interfaces.IRegisterSchema, RegisterSchema),
        (interfaces.IForgotPasswordSchema, ForgotPasswordSchema),
        (interfaces.IResetPasswordSchema, ResetPasswordSchema),
        (interfaces.IActivateSchema, ActivateSchema)
    ]

    for iface, schema in schemas:
        if not config.registry.queryUtility(iface):
            config.registry.registerUtility(schema, iface)
