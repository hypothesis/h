# -*- coding: utf-8 -*-
from pkg_resources import resource_stream

import colander
import deform
from pyramid.session import check_csrf_token

from h import i18n
from h.accounts.models import User

_ = i18n.TranslationString

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


def email_exists(node, value):
    '''Colander validator that ensures a user with this email exists.'''
    user = User.get_by_email(value)
    if not user:
        msg = _('We have no user with the email address "{}". Try correcting '
                'this address or try another.')
        raise colander.Invalid(node, msg)


def unique_email(node, value):
    '''Colander validator that ensures no user with this email exists.'''
    user = User.get_by_email(value)
    if user:
        msg = _("Sorry, an account with this email address already exists. "
                "Try logging in instead.")
        raise colander.Invalid(node, msg)


def unique_username(node, value):
    '''Colander validator that ensures the username does not exist.'''
    user = User.get_by_username(value)
    if user:
        msg = _("Sorry, an account with this username already exists. "
                "Please enter another one.")
        raise colander.Invalid(node, msg)


def unblacklisted_username(node, value, blacklist=None):
    '''Colander validator that ensures the username is not blacklisted.'''
    if blacklist is None:
        blacklist = get_blacklist()
    if value.lower() in blacklist:
        # We raise a generic "user with this name already exists" error so as
        # not to make explicit the presence of a blacklist.
        msg = _("Sorry, an account with this username already exists. "
                "Please enter another one.")
        raise colander.Invalid(node, msg)


def matching_emails(node, value):
    """Colander validator that ensures email and emailAgain fields match."""
    if value.get("email") != value.get("emailAgain"):
        exc = colander.Invalid(node)
        exc["emailAgain"] = _("The emails must match")
        raise exc


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

        username = value.get('username')
        password = value.get('password')

        user = User.get_by_username(username)
        if user is None:
            user = User.get_by_email(username)

        if user is None:
            err = colander.Invalid(node)
            err['username'] = _('User does not exist.')
            raise err

        if not User.validate_user(user, password):
            err = colander.Invalid(node)
            err['password'] = _('Incorrect password. Please try again.')
            raise err

        if not user.is_activated:
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


class ProfileSchema(CSRFSchema):

    """
    Validates a user profile form.

    This form is broken into multiple parts, for updating the email address,
    password, and subscriptions, so multiple fields are nullable.
    """

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

    def validator(self, node, value):
        super(ProfileSchema, self).validator(node, value)

        # Check that emails match
        matching_emails(node, value)


def includeme(config):
    pass
