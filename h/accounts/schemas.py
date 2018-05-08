# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from codecs import open
import logging

import colander
import deform
from itsdangerous import BadData, SignatureExpired
from jinja2 import Markup

from h import i18n, models, validators
from h.accounts import util
from h.services.user import UserNotActivated
from h.models.user import (
    DISPLAY_NAME_MAX_LENGTH,
    EMAIL_MAX_LENGTH,
    USERNAME_MAX_LENGTH,
    USERNAME_MIN_LENGTH,
    USERNAME_PATTERN,
)
from h.schemas.base import CSRFSchema, JSONSchema

_ = i18n.TranslationString
log = logging.getLogger(__name__)

PASSWORD_MIN_LENGTH = 2  # FIXME: this is ridiculous
USERNAME_BLACKLIST = None


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
    user = models.User.get_by_email(request.db, value, request.authority)
    if user and user.userid != request.authenticated_userid:
        msg = _("Sorry, an account with this email address already exists.")
        raise colander.Invalid(node, msg)


def unique_username(node, value):
    '''Colander validator that ensures the username does not exist.'''
    request = node.bindings['request']
    user = models.User.get_by_username(request.db, value, request.authority)
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


def privacy_acceptance_validator(node, value):
    '''Colander validator that ensures privacy acceptance checkbox checked'''
    if value is False:
        msg = _("Acceptance of the privacy policy is required")
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


def _privacy_accepted_message():
    terms_links = {
        'privacy_policy': '<a class="link" href="{href}">{text}</a>'.format(
            href='https://web.hypothes.is/privacy/',
            text=_('privacy policy'),
        ),
        'terms_of_service': '<a class="link" href="{href}">{text}</a>'.format(
            href='https://web.hypothes.is/terms-of-service/',
            text=_('terms of service'),
        ),
        'community_guidelines': '<a class="link" href="{href}">{text}</a>'.format(
            href='https://web.hypothes.is/community-guidelines/',
            text=_('community guidelines'),
        ),
    }

    privacy_msg = _('I have read and agree to the {privacy}, {tos}, and {community}.').format(
        privacy=terms_links['privacy_policy'],
        tos=terms_links['terms_of_service'],
        community=terms_links['community_guidelines']
    )

    return privacy_msg


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
        user_password_service = request.find_service(name='user_password')

        try:
            user = user_service.fetch_for_login(username_or_email=username)
        except UserNotActivated:
            err = colander.Invalid(node)
            err['username'] = _("Please check your email and open the link "
                                "to activate your account.")
            raise err

        if user is None:
            err = colander.Invalid(node)
            err['username'] = _('User does not exist.')
            raise err

        if not user_password_service.check_password(user, password):
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
        user = models.User.get_by_email(request.db, email, request.authority)

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

    privacy_accepted = colander.SchemaNode(
        colander.Boolean(),
        description=Markup(_privacy_accepted_message()),
        validator=privacy_acceptance_validator,
        widget=deform.widget.CheckboxWidget(
            omit_label=True,
            css_class='form-checkbox--inline'
        ),
    )


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

        user = models.User.get_by_username(request.db, username, request.authority)
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


class EmailChangeSchema(CSRFSchema):
    email = email_node(title=_('Email address'))
    # No validators: all validation is done on the email field
    password = password_node(title=_('Confirm password'),
                             hide_until_form_active=True)

    def validator(self, node, value):
        super(EmailChangeSchema, self).validator(node, value)
        exc = colander.Invalid(node)
        request = node.bindings['request']
        svc = request.find_service(name='user_password')
        user = request.user

        if not svc.check_password(user, value.get('password')):
            exc['password'] = _('Wrong password.')

        if exc.children:
            raise exc


class PasswordChangeSchema(CSRFSchema):
    password = password_node(title=_('Current password'),
                             inactive_label=_('Password'))
    new_password = password_node(title=_('New password'),
                                 hide_until_form_active=True)
    # No validators: all validation is done on the new_password field and we
    # merely assert that the confirmation field is the same.
    new_password_confirm = colander.SchemaNode(
        colander.String(),
        title=_('Confirm new password'),
        widget=deform.widget.PasswordWidget(),
        hide_until_form_active=True)

    def validator(self, node, value):
        super(PasswordChangeSchema, self).validator(node, value)
        exc = colander.Invalid(node)
        request = node.bindings['request']
        svc = request.find_service(name='user_password')
        user = request.user

        if value.get('new_password') != value.get('new_password_confirm'):
            exc['new_password_confirm'] = _('The passwords must match')

        if not svc.check_password(user, value.get('password')):
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
        validator=validators.Length(max=DISPLAY_NAME_MAX_LENGTH),
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


class CreateUserAPISchema(JSONSchema):
    """Validate a user JSON object."""

    schema = {
        'type': 'object',
        'properties': {
            'authority': {
                'type': 'string',
                'format': 'hostname',
            },
            'username': {
                'type': 'string',
                'minLength': USERNAME_MIN_LENGTH,
                'maxLength': USERNAME_MAX_LENGTH,
                'pattern': '^[A-Za-z0-9._]+$',
            },
            'email': {
                'type': 'string',
                'format': 'email',
                'maxLength': EMAIL_MAX_LENGTH,
            },
            'display_name': {
                'type': 'string',
                'maxLength': DISPLAY_NAME_MAX_LENGTH,
            },
        },
        'required': [
            'authority',
            'username',
            'email',
        ],
    }


class UpdateUserAPISchema(JSONSchema):
    """Validate a user JSON object."""

    schema = {
        'type': 'object',
        'properties': {
            'email': {
                'type': 'string',
                'format': 'email',
                'maxLength': EMAIL_MAX_LENGTH,
            },
            'display_name': {
                'type': 'string',
                'maxLength': DISPLAY_NAME_MAX_LENGTH,
            },
        },
    }


def includeme(config):
    pass
