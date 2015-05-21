# -*- coding: utf-8 -*-
from pkg_resources import resource_stream

import colander
import deform
from horus import interfaces
from horus.schemas import email_exists, unique_email
from pyramid.settings import asbool
from pyramid.session import check_csrf_token

from h.models import _

USERNAME_BLACKLIST = None


@colander.deferred
def deferred_csrf_token(node, kw):
    request = kw.get('request')
    return request.session.get_csrf_token()


def get_blacklist():
    global USERNAME_BLACKLIST
    if USERNAME_BLACKLIST is None:
        USERNAME_BLACKLIST = set(
            l.strip().lower()
            for l in resource_stream(__package__, 'blacklist')
        )
    return USERNAME_BLACKLIST


def unique_username(node, value):
    '''Colander validator that ensures the username does not exist.'''
    request = node.bindings['request']
    user_ctor = request.registry.getUtility(interfaces.IUserClass)
    user = user_ctor.get_by_username(request, value)
    if user:
        strings = request.registry.getUtility(interfaces.IUIStrings)
        raise colander.Invalid(node, strings.registration_username_exists)


def unblacklisted_username(node, value, blacklist=None):
    '''Colander validator that ensures the username is not blacklisted.'''
    if blacklist is None:
        blacklist = get_blacklist()
    if value.lower() in blacklist:
        # We raise a generic "user with this name already exists" error so as
        # not to make explicit the presence of a blacklist.
        req = node.bindings['request']
        str_ = req.registry.getUtility(interfaces.IUIStrings)
        raise colander.Invalid(node, str_.registration_username_exists)


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

    def validator(self, form, value):
        request = form.bindings['request']
        check_csrf_token(request)


class LoginSchema(CSRFSchema):
    username = colander.SchemaNode(colander.String())
    password = colander.SchemaNode(
        colander.String(),
        widget=deform.widget.PasswordWidget()
    )

    def validator(self, node, value):
        super(LoginSchema, self).validator(node, value)
        request = node.bindings['request']
        registry = request.registry
        settings = registry.settings

        allow_email_auth = asbool(
            settings.get('horus.allow_email_auth', False)
        )
        allow_inactive_login = asbool(
            settings.get('horus.allow_inactive_login', False)
        )
        require_activation = asbool(
            settings.get('horus.require_activation', True)
        )

        user_ctor = registry.getUtility(interfaces.IUserClass)

        username = value.get('username')
        password = value.get('password')

        user = user_ctor.get_by_username(request, username)
        if user is None and allow_email_auth:
            user = user_ctor.get_by_email(request, username)

        if user is None:
            err = colander.Invalid(node)
            err['username'] = _('User does not exist.')
            raise err

        if not user_ctor.validate_user(user, password):
            err = colander.Invalid(node)
            err['password'] = _('Incorrect password. Please try again.')
            raise err

        if not allow_inactive_login and require_activation \
                and not user.is_activated:
            reason = _('Your account is not active. Please check your e-mail.')
            raise colander.Invalid(node, reason)

        value['user'] = user


class ForgotPasswordSchema(CSRFSchema):
    email = colander.SchemaNode(
        colander.String(),
        validator=colander.All(colander.Email(), email_exists)
    )


class RegisterSchema(CSRFSchema):
    username = colander.SchemaNode(
        colander.String(),
        validator=colander.All(
            colander.Length(min=3, max=15),
            colander.Regex('(?i)^[A-Z0-9._]+$'),
            unique_username,
            unblacklisted_username,
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
        title=_("Security Code")
    )
    password = colander.SchemaNode(
        colander.String(),
        title=_('New Password'),
        validator=colander.Length(min=2),
        widget=deform.widget.PasswordWidget()
    )


class EditProfileSchema(CSRFSchema):
    username = colander.SchemaNode(colander.String())
    pwd = colander.SchemaNode(
        colander.String(),
        widget=deform.widget.PasswordWidget(),
        default='',
        missing=colander.null
    )
    email = colander.SchemaNode(
        colander.String(),
        validator=colander.All(colander.Email(), unique_email),
        default='',
        missing=colander.null
    )
    emailAgain = colander.SchemaNode(
        colander.String(),
        default='',
        missing=colander.null,
    )
    password = colander.SchemaNode(
        colander.String(),
        title=_('Password'),
        widget=deform.widget.PasswordWidget(),
        default='',
        missing=colander.null
    )
    subscriptions = colander.SchemaNode(
        colander.String(),
        missing=colander.null,
        default=''
    )


def includeme(config):
    registry = config.registry

    schemas = [
        (interfaces.ILoginSchema, LoginSchema),
        (interfaces.IRegisterSchema, RegisterSchema),
        (interfaces.IForgotPasswordSchema, ForgotPasswordSchema),
        (interfaces.IResetPasswordSchema, ResetPasswordSchema),
        (interfaces.IProfileSchema, EditProfileSchema)
    ]

    for iface, imp in schemas:
        if not registry.queryUtility(iface):
            registry.registerUtility(imp, iface)
