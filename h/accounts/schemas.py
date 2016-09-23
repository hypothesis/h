# -*- coding: utf-8 -*-
from codecs import open
import logging

import colander
import deform
from pyramid.session import check_csrf_token
from itsdangerous import BadData, SignatureExpired

from h import i18n, models, validators
from h.accounts import util
from h.accounts.services import UserNotActivated, UserNotKnown
from h.models.user import (
    EMAIL_MAX_LENGTH,
    PASSWORD_MIN_LENGTH,
    USERNAME_MAX_LENGTH,
    USERNAME_MIN_LENGTH,
    USERNAME_PATTERN,
)

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
            with open('h/accounts/blacklist', encoding='utf-8') as fp:
                blacklist = fp.readlines()
        except (IOError, ValueError):
            log.exception('unable to load blacklist')
            blacklist = []
        USERNAME_BLACKLIST = set(l.strip().lower() for l in blacklist)
    return USERNAME_BLACKLIST


def unique_email(node, value):
    '''Colander validator that ensures no user with this email exists.'''
    request = node.bindings['request']
    user = models.User.get_by_email(request.db, value)
    if user and user.userid != request.authenticated_userid:
        msg = _("Sorry, an account with this email address already exists.")
        raise colander.Invalid(node, msg)


def unique_username(node, value):
    '''Colander validator that ensures the username does not exist.'''
    request = node.bindings['request']
    user = models.User.get_by_username(request.db, value)
    if user:
        msg = _("This username is already taken.")
        raise colander.Invalid(node, msg)


def email_node(**kwargs):
    """Return a Colander schema node for a new user email."""
    return colander.SchemaNode(
        colander.String(),
        validator=colander.All(
            validators.Length(max=EMAIL_MAX_LENGTH),
            validators.Email(),
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
    """Return a Colander schema node for an existing user password."""
    kwargs.setdefault('widget', deform.widget.PasswordWidget())
    return colander.SchemaNode(
        colander.String(),
        **kwargs)


def new_password_node(**kwargs):
    """Return a Colander schema node for a new user password."""
    kwargs.setdefault('widget', deform.widget.PasswordWidget())
    return colander.SchemaNode(
        colander.String(),
        validator=validators.Length(min=PASSWORD_MIN_LENGTH),
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
        title=_('Username / email'),
        widget=deform.widget.TextInputWidget(autofocus=True),
    )
    password = colander.SchemaNode(
        colander.String(),
        title=_('Password'),
        widget=deform.widget.PasswordWidget()
    )

    def validator(self, node, value):
        super(LoginSchema, self).validator(node, value)

        request = node.bindings['request']
        username = value.get('username')
        password = value.get('password')

        user_service = request.find_service(name='user')

        try:
            user = user_service.login(username_or_email=username,
                                      password=password)
        except UserNotKnown:
            err = colander.Invalid(node)
            err['username'] = _('User does not exist.')
            raise err
        except UserNotActivated:
            err = colander.Invalid(node)
            err['username'] = _("Please check your email and open the link "
                                "to activate your account.")
            raise err

        if user is None:
            err = colander.Invalid(node)
            err['password'] = _('Wrong password.')
            raise err

        value['user'] = user


class ForgotPasswordSchema(CSRFSchema):
    email = colander.SchemaNode(
        colander.String(),
        validator=colander.All(validators.Email()),
        title=_('Email address'),
        widget=deform.widget.TextInputWidget(template='emailinput',
                                             autofocus=True),
    )

    def validator(self, node, value):
        super(ForgotPasswordSchema, self).validator(node, value)

        request = node.bindings['request']
        email = value.get('email')
        user = models.User.get_by_email(request.db, email)

        if user is None:
            err = colander.Invalid(node)
            err['email'] = _('Unknown email address.')
            raise err

        value['user'] = user


class RegisterSchema(CSRFSchema):
    username = colander.SchemaNode(
        colander.String(),
        validator=colander.All(
            validators.Length(min=USERNAME_MIN_LENGTH,
                              max=USERNAME_MAX_LENGTH),
            colander.Regex(
                USERNAME_PATTERN,
                msg=_("Must have only letters, numbers, periods, and "
                      "underscores.")),
            unique_username,
            unblacklisted_username,
        ),
        title=_('Username'),
        hint=_('Must be between {min} and {max} characters, containing only '
               'letters, numbers, periods, and underscores.').format(
            min=USERNAME_MIN_LENGTH,
            max=USERNAME_MAX_LENGTH
        ),
        widget=deform.widget.TextInputWidget(autofocus=True),
    )
    email = email_node(title=_('Email address'))
    password = new_password_node(title=_('Password'))


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
            raise colander.Invalid(node, _('Reset code has expired. Please reset your password again'))
        except BadData:
            raise colander.Invalid(node, _('Wrong reset code.'))

        user = models.User.get_by_username(request.db, username)
        if user is None:
            raise colander.Invalid(node, _('Your reset code is not valid'))
        if user.password_updated is not None and timestamp < user.password_updated:
            raise colander.Invalid(node,
                                   _('This reset code has already been used.'))
        return user


class ResetPasswordSchema(CSRFSchema):
    # N.B. this is the field into which the user puts their reset code, but we
    # call it `user` because when validated, it will return a `User` object.
    user = colander.SchemaNode(
        ResetCode(),
        title=_('Reset code'),
        hint=_('This will be emailed to you.'),
        widget=deform.widget.TextInputWidget(disable_autocomplete=True))
    password = new_password_node(
        title=_('New password'),
        widget=deform.widget.PasswordWidget(disable_autocomplete=True))


class LegacyEmailChangeSchema(CSRFSchema):
    email = email_node(title=_('New email address'))
    # No validators: all validation is done on the email field and we merely
    # assert that the confirmation field is the same.
    email_confirm = colander.SchemaNode(
        colander.String(),
        title=_('Confirm new email address'),
        widget=deform.widget.TextInputWidget(template='emailinput'))
    password = new_password_node(title=_('Current password'))

    def validator(self, node, value):
        super(LegacyEmailChangeSchema, self).validator(node, value)
        exc = colander.Invalid(node)
        request = node.bindings['request']
        user = request.authenticated_user

        if value.get('email') != value.get('email_confirm'):
            exc['email_confirm'] = _('The emails must match')

        if not user.check_password(value.get('password')):
            exc['password'] = _('Wrong password.')

        if exc.children:
            raise exc


class EmailChangeSchema(CSRFSchema):
    email = email_node(title=_('Email address'))
    # No validators: all validation is done on the email field
    password = password_node(title=_('Confirm password'))

    def validator(self, node, value):
        super(EmailChangeSchema, self).validator(node, value)
        exc = colander.Invalid(node)
        request = node.bindings['request']
        user = request.authenticated_user

        if not user.check_password(value.get('password')):
            exc['password'] = _('Wrong password.')

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

        if not user.check_password(value.get('password')):
            exc['password'] = _('Wrong password.')

        if exc.children:
            raise exc


def validate_url(node, cstruct):
    try:
        util.validate_url(cstruct)
    except ValueError as exc:
        raise colander.Invalid(node, str(exc))


def validate_orcid(node, cstruct):
    try:
        util.validate_orcid(cstruct)
    except ValueError as exc:
        raise colander.Invalid(node, str(exc))


class EditProfileSchema(CSRFSchema):
    display_name = colander.SchemaNode(
        colander.String(),
        missing=None,
        validator=validators.Length(max=30),
        title=_('Display name'))

    description = colander.SchemaNode(
        colander.String(),
        missing=None,
        validator=validators.Length(max=250),
        widget=deform.widget.TextAreaWidget(
            max_length=250,
            rows=4,
        ),
        title=_('Description'))

    location = colander.SchemaNode(
        colander.String(),
        missing=None,
        validator=validators.Length(max=100),
        title=_('Location'))

    link = colander.SchemaNode(
        colander.String(),
        missing=None,
        validator=colander.All(
            validators.Length(max=250),
            validate_url),
        title=_('Link'))

    orcid = colander.SchemaNode(
        colander.String(),
        missing=None,
        validator=validate_orcid,
        title=_('ORCID'),
        hint=_('ORCID provides a persistent identifier for researchers (see orcid.org).'))


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
