# -*- coding: utf-8 -*-
from pkg_resources import resource_stream
import logging

import colander
import deform
from pyramid.session import check_csrf_token
from itsdangerous import BadData, SignatureExpired

from h import i18n
from h.accounts import models

_ = i18n.TranslationString
log = logging.getLogger(__name__)

USERNAME_BLACKLIST = None


@colander.deferred
def deferred_csrf_token(node, kw):
    request = kw.get('request')
    return request.session.get_csrf_token()


def get_blacklist():
    global USERNAME_BLACKLIST
    if USERNAME_BLACKLIST is None:
        # Try to load the blacklist file from disk. If, for whatever reason, we
        # can't load the file, then don't crash out, just log a warning about
        # the problem.
        try:
            blacklist = resource_stream(__package__, 'blacklist').readlines()
        except IOError:
            log.exception('unable to load blacklist')
            blacklist = []
        USERNAME_BLACKLIST = set(l.strip().lower() for l in blacklist)
    return USERNAME_BLACKLIST


def unique_email(node, value):
    '''Colander validator that ensures no user with this email exists.'''
    user = models.User.get_by_email(value)
    if user:
        msg = _("Sorry, an account with this email address already exists.")
        raise colander.Invalid(node, msg)


def unique_username(node, value):
    '''Colander validator that ensures the username does not exist.'''
    user = models.User.get_by_username(value)
    if user:
        msg = _("Sorry, an account with this username already exists. "
                "Please enter another one.")
        raise colander.Invalid(node, msg)


def email_node(**kwargs):
    """Return a Colander schema node for a new user email."""
    return colander.SchemaNode(
        colander.String(),
        validator=colander.All(
            colander.Length(max=models.EMAIL_MAX_LENGTH),
            colander.Email(),
            unique_email,
        ),
        widget=deform.widget.TextInputWidget(template='emailinput'),
        **kwargs)


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


def password_node(**kwargs):
    """Return a Colander schema node for a user password."""
    kwargs.setdefault('widget', deform.widget.PasswordWidget())
    return colander.SchemaNode(
        colander.String(),
        validator=colander.Length(min=models.PASSWORD_MIN_LENGTH),
        **kwargs)


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
    username = colander.SchemaNode(
        colander.String(),
        title=_('Username or email address:'),
        widget=deform.widget.TextInputWidget(autofocus=True),
    )
    password = colander.SchemaNode(
        colander.String(),
        title=_('Password:'),
        widget=deform.widget.PasswordWidget()
    )

    def validator(self, node, value):
        super(LoginSchema, self).validator(node, value)

        username = value.get('username')
        password = value.get('password')

        user = models.User.get_by_username(username)
        if user is None:
            user = models.User.get_by_email(username)

        if user is None:
            err = colander.Invalid(node)
            err['username'] = _('User does not exist.')
            raise err

        if not models.User.validate_user(user, password):
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
        validator=colander.All(colander.Email()),
        title=_('Please enter your email address:'),
        widget=deform.widget.TextInputWidget(template='emailinput',
                                             autofocus=True),
    )

    def validator(self, node, value):
        super(ForgotPasswordSchema, self).validator(node, value)

        email = value.get('email')
        user = models.User.get_by_email(email)

        if user is None:
            err = colander.Invalid(node)
            err['email'] = _('We have no user with the email address '
                             '"{email}". Try correcting this address or try '
                             'another.').format(email=email)
            raise err

        value['user'] = user


class RegisterSchema(CSRFSchema):
    username = colander.SchemaNode(
        colander.String(),
        validator=colander.All(
            colander.Length(
                min=models.USERNAME_MIN_LENGTH,
                max=models.USERNAME_MAX_LENGTH),
            colander.Regex('(?i)^[A-Z0-9._]+$'),
            unique_username,
            unblacklisted_username,
        ),
        title=_('Username:'),
        hint=_('between {min} and {max} characters').format(
            min=models.USERNAME_MIN_LENGTH,
            max=models.USERNAME_MAX_LENGTH
        ),
        widget=deform.widget.TextInputWidget(autofocus=True),
    )
    email = email_node(title=_('Email address:'))
    password = password_node(title=_('Password:'))


class ResetCode(colander.SchemaType):

    """Schema type transforming a reset code to a user and back."""

    def serialize(self, node, appstruct):
        if appstruct is colander.null:
            return colander.null
        if not isinstance(appstruct, models.User):
            raise colander.Invalid(node, '%r is not a User' % appstruct)
        request = node.bindings['request']
        serializer = request.registry.password_reset_serializer
        return serializer.dumps(appstruct.username)

    def deserialize(self, node, cstruct):
        if cstruct is colander.null:
            return colander.null

        request = node.bindings['request']
        serializer = request.registry.password_reset_serializer

        try:
            (username, timestamp) = serializer.loads(cstruct,
                                                     max_age=72*3600,
                                                     return_timestamp=True)
        except SignatureExpired:
            raise colander.Invalid(node, _('Your reset code has expired'))
        except BadData:
            raise colander.Invalid(node, _('Your reset code is not valid'))

        user = models.User.get_by_username(username)
        if user is None:
            raise colander.Invalid(node, _('Your reset code is not valid'))
        if user.password_updated is not None and timestamp < user.password_updated:
            raise colander.Invalid(node,
                                   _('You have already reset your password'))
        return user


class ResetPasswordSchema(CSRFSchema):
    # N.B. this is the field into which the user puts their reset code, but we
    # call it `user` because when validated, it will return a `User` object.
    user = colander.SchemaNode(
        ResetCode(),
        title=_('Your reset code:'),
        hint=_('this will be emailed to you'),
        widget=deform.widget.TextInputWidget(disable_autocomplete=True))
    password = password_node(
        title=_('New password:'),
        widget=deform.widget.PasswordWidget(disable_autocomplete=True))


class EmailChangeSchema(CSRFSchema):
    email = email_node(title=_('New email address'))
    # No validators: all validation is done on the email field and we merely
    # assert that the confirmation field is the same.
    email_confirm = colander.SchemaNode(
        colander.String(),
        title=_('Confirm new email address'),
        widget=deform.widget.TextInputWidget(template='emailinput'))
    password = password_node(title=_('Current password'))

    def validator(self, node, value):
        super(EmailChangeSchema, self).validator(node, value)
        exc = colander.Invalid(node)
        request = node.bindings['request']
        user = request.authenticated_user

        if value.get('email') != value.get('email_confirm'):
            exc['email_confirm'] = _('The emails must match')

        if not models.User.validate_user(user, value.get('password')):
            exc['password'] = _('Incorrect password. Please try again.')

        if exc.children:
            raise exc


class PasswordChangeSchema(CSRFSchema):
    password = password_node(title=_('Current password'))
    new_password = password_node(title=_('New password'))
    # No validators: all validation is done on the new_password field and we
    # merely assert that the confirmation field is the same.
    new_password_confirm = colander.SchemaNode(
        colander.String(),
        title=_('Confirm new password'),
        widget=deform.widget.PasswordWidget())

    def validator(self, node, value):
        super(PasswordChangeSchema, self).validator(node, value)
        exc = colander.Invalid(node)
        request = node.bindings['request']
        user = request.authenticated_user

        if value.get('new_password') != value.get('new_password_confirm'):
            exc['new_password_confirm'] = _('The passwords must match')

        if not models.User.validate_user(user, value.get('password')):
            exc['password'] = _('Incorrect password. Please try again.')

        if exc.children:
            raise exc


class NotificationsSchema(CSRFSchema):
    types = (('reply', _('Email me when someone replies to one of my annotations.'),),)

    notifications = colander.SchemaNode(
        colander.Set(),
        widget=deform.widget.CheckboxChoiceWidget(
            omit_label=True,
            values=types),
    )


def includeme(config):
    pass
