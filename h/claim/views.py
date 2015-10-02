# -*- coding: utf-8 -*-
import logging

import deform
from pyramid import httpexceptions as exc
from pyramid.view import view_config

from h import i18n
from h.accounts.models import User
from h.accounts.events import LoginEvent
from h.claim import schemas

_ = i18n.TranslationString

log = logging.getLogger(__name__)


@view_config(route_name='claim_account',
             request_method='GET',
             renderer='h:claim/templates/claim_account.html.jinja2')
def claim_account(request):
    _validate_request(request)

    form = _form_for_update_account(request)
    return {'form': form.render()}


@view_config(route_name='claim_account',
             request_method='POST',
             renderer='h:claim/templates/claim_account.html.jinja2')
def update_account(request):
    user = _validate_request(request)

    form = _form_for_update_account(request)
    try:
        appstruct = form.validate(request.POST.items())
    except deform.ValidationFailure:
        return {'form': form.render()}

    # The token is valid and the form validates, so we can go ahead and claim
    # the account:
    user.password = appstruct['password']

    msg = _('Your account has been successfully claimed.')
    request.session.flash(msg, 'success')

    request.registry.notify(LoginEvent(request, user))
    return exc.HTTPFound(location=request.route_url('index'))


def _validate_request(request):
    """
    Check that the passed request is appropriate for proceeding with account
    claim. Asserts that:

    - the 'claim' feature is toggled on
    - no-one is logged in
    - the claim token is provided and authentic
    - the user referred to in the token exists
    - the user referred to in the token has not already claimed their account

    and raises for redirect or 404 otherwise.
    """
    if not request.feature('claim'):
        raise exc.HTTPNotFound()

    # If signed in, redirect to stream
    if request.authenticated_userid is not None:
        _perform_logged_in_redirect(request)

    payload = _validate_token(request)
    if payload is None:
        raise exc.HTTPNotFound()

    user = User.get_by_userid(request.domain, payload['userid'])
    if user is None:
        log.warn('got claim token with invalid userid=%r', payload['userid'])
        raise exc.HTTPNotFound()

    # User already has a password? Claimed already.
    if user.password:
        _perform_already_claimed_redirect(request)

    return user


def _form_for_update_account(request):
    schema = schemas.UpdateAccountSchema().bind(request=request)
    form = deform.Form(schema, buttons=(_('Claim account'),))
    return form


def _perform_already_claimed_redirect(request):
    msg = _('This account has already been claimed.')
    request.session.flash(msg, 'error')
    raise exc.HTTPFound(location=request.route_url('stream'))


def _perform_logged_in_redirect(request):
    msg = _('You are already signed in, please log out to claim an account.')
    request.session.flash(msg, 'error')
    raise exc.HTTPFound(location=request.route_url('stream'))


def _validate_token(request):
    try:
        token = request.matchdict['token']
    except KeyError:
        return None

    try:
        validated = request.registry.claim_serializer.loads(token)
    except ValueError:
        return None

    return validated


def includeme(config):
    config.add_route('claim_account', '/claim_account/{token}')
    config.scan(__name__)
