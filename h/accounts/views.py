# -*- coding: utf-8 -*-
import datetime
import json

import deform
from pyramid import httpexceptions
from pyramid.view import view_config, view_defaults
from pyramid.security import forget, remember
from pyramid_mailer import get_mailer
from pyramid_mailer.message import Message

from h.resources import Application
from h.notification.models import Subscriptions
from h import i18n
from h.accounts.models import User
from h.accounts.models import Activation
from h.accounts.events import ActivationEvent
from h.accounts.events import PasswordResetEvent
from h.accounts.events import LogoutEvent
from h.accounts.events import LoginEvent
from h.accounts.events import RegistrationEvent
from h.accounts import schemas
from h import session

_ = i18n.TranslationString


def ajax_form(request, result):
    if isinstance(result, httpexceptions.HTTPRedirection):
        request.response.headers.extend(result.headers)
        result = {'status': 'okay'}
    elif isinstance(result, httpexceptions.HTTPError):
        request.response.status_code = result.code
        result = {'status': 'failure', 'reason': str(result)}
    elif 'errors' in result:
        request.response.status_code = result.pop('code', 400)
        result['status'] = 'failure'

    result['flash'] = session.pop_flash(request)

    return result


def validate_form(form, data):
    """Validate POST payload data for a form."""
    try:
        appstruct = form.validate(data)
    except deform.ValidationFailure as err:
        return {'errors': err.error.asdict()}, None
    else:
        return None, appstruct


def view_auth_defaults(fn, *args, **kwargs):
    kwargs.setdefault('accept', 'text/html')
    kwargs.setdefault('renderer', 'h:templates/auth.html.jinja2')
    return view_defaults(*args, **kwargs)(fn)


@view_config(accept='application/json', renderer='json',
             context='pyramid.exceptions.BadCSRFToken')
def bad_csrf_token(context, request):
    request.response.status_code = 403
    reason = _('Session is invalid. Please try again.')
    return {
        'status': 'failure',
        'reason': reason,
        'model': session.model(request),
    }


class AjaxFormViewMapper(object):
    def __init__(self, **kw):
        self.attr = kw['attr']

    def __call__(self, view):
        def wrapper(context, request):
            if request.method == 'POST':
                data = request.json_body
                data.update(request.params)
                request.content_type = 'application/x-www-form-urlencoded'
                request.POST.clear()
                request.POST.update(data)

            inst = view(request)
            meth = getattr(inst, self.attr)
            result = meth()

            if isinstance(result, httpexceptions.HTTPRedirection):
                result.location = request.path_url
                return result

            result = ajax_form(request, result)

            model = result.setdefault('model', {})
            model.update(session.model(request))

            return result

        return wrapper


@view_auth_defaults
@view_config(attr='login', route_name='login')
@view_config(attr='logout', route_name='logout')
class AuthController(object):
    def __init__(self, request):
        self.request = request
        self.schema = schemas.LoginSchema().bind(request=self.request)
        self.form = deform.Form(self.schema)

        self.login_redirect = self.request.route_url('stream')
        self.logout_redirect = self.request.route_url('index')

    def login(self):
        if self.request.authenticated_userid is not None:
            return httpexceptions.HTTPFound(location=self.login_redirect)

        err, appstruct = validate_form(self.form, self.request.POST.items())
        if err is not None:
            return err

        user = appstruct['user']
        user.last_login_date = datetime.datetime.utcnow()

        self.request.registry.notify(LoginEvent(self.request, user))

        userid = 'acct:{}@{}'.format(user.username, self.request.domain)
        headers = remember(self.request, userid)

        return httpexceptions.HTTPFound(location=self.login_redirect,
                                        headers=headers)

    def logout(self):
        self.request.registry.notify(LogoutEvent(self.request))
        self.request.session.invalidate()
        self.request.session.flash(_('You have logged out.'), 'success')
        headers = forget(self.request)
        return httpexceptions.HTTPFound(location=self.logout_redirect,
                                        headers=headers)


@view_defaults(accept='application/json', context=Application, renderer='json')
@view_config(attr='login', request_param='__formid__=login')
@view_config(attr='logout', request_param='__formid__=logout')
class AjaxAuthController(AuthController):
    __view_mapper__ = AjaxFormViewMapper


@view_auth_defaults
@view_config(attr='forgot_password',
             route_name='forgot_password',
             request_method='POST')
@view_config(attr='forgot_password_form',
             route_name='forgot_password',
             request_method='GET')
@view_config(attr='reset_password',
             route_name='reset_password',
             request_method='POST')
@view_config(attr='reset_password_form',
             route_name='reset_password',
             request_method='GET')
class ForgotPasswordController(object):

    """Controller for handling password reset forms."""

    def __init__(self, request):
        self.request = request
        self.forgot_password_redirect = self.request.route_url('index')
        self.reset_password_redirect = self.request.route_url('index')

    def forgot_password(self):
        """
        Handle submission of the forgot password form.

        Validates that the email is one we know about, and then generates a new
        activation for the associated user, and dispatches a "reset your
        password" email which contains a token and/or link to the reset
        password form.
        """
        schema = schemas.ForgotPasswordSchema().bind(request=self.request)
        form = deform.Form(schema)

        # Nothing to do here for logged-in users
        if self.request.authenticated_userid is not None:
            return httpexceptions.HTTPFound(
                location=self.forgot_password_redirect)

        err, appstruct = validate_form(form, self.request.POST.items())
        if err is not None:
            return err

        # If the validation passes, we assume the user exists.
        #
        # TODO: fix this latent race condition by returning a user object in
        # the appstruct.
        user = User.get_by_email(appstruct['email'])

        # Create a new activation for this user. Any previous activation will
        # get overwritten.
        activation = Activation()
        self.request.db.add(activation)
        user.activation = activation

        # Write the new activation to the database in order to set up the
        # foreign key field and generate the code.
        self.request.db.flush()

        # Send the reset password email
        code = user.activation.code
        link = reset_password_link(self.request, code)
        message = reset_password_email(user, code, link)
        mailer = get_mailer(self.request)
        mailer.send(message)

        self.request.session.flash(_("Please check your email to finish "
                                     "resetting your password."),
                                   "success")

        return httpexceptions.HTTPFound(location=self.reset_password_redirect)

    # FIXME: generate a form here and progressively enhance it rather than
    # relying entirely on Angular.
    def forgot_password_form(self):
        """Render the forgot password form."""
        if self.request.authenticated_userid is not None:
            return httpexceptions.HTTPFound(
                location=self.forgot_password_redirect)

        return {}

    def reset_password(self):
        """
        Handle submission of the reset password form.

        This function checks that the activation code (i.e. reset token)
        provided by the form is valid, retrieves the user associated with the
        activation code, and resets their password.
        """
        schema = schemas.ResetPasswordSchema().bind(request=self.request)
        form = deform.Form(schema)

        code = self.request.matchdict.get('code')
        if code is None:
            return httpexceptions.HTTPNotFound()

        activation = Activation.get_by_code(code)
        if activation is None:
            return httpexceptions.HTTPNotFound()

        user = User.get_by_activation(activation)
        if user is None:
            return httpexceptions.HTTPNotFound()

        if self.request.method != 'POST':
            return httpexceptions.HTTPMethodNotAllowed()

        err, appstruct = validate_form(form, self.request.POST.items())
        if err is not None:
            return err

        user.password = appstruct['password']
        self.request.db.delete(activation)

        self.request.session.flash(_('Your password has been reset!'),
                                   'success')
        self.request.registry.notify(PasswordResetEvent(self.request, user))

        return httpexceptions.HTTPFound(location=self.reset_password_redirect)

    # FIXME: generate a form here and progressively enhance it rather than
    # relying entirely on Angular.
    def reset_password_form(self):
        """Render the reset password form."""
        return {}


@view_defaults(accept='application/json', context=Application, renderer='json')
@view_config(
    attr='forgot_password',
    request_param='__formid__=forgot_password'
)
@view_config(
    attr='reset_password',
    request_param='__formid__=reset_password'
)
class AjaxForgotPasswordController(ForgotPasswordController):
    __view_mapper__ = AjaxFormViewMapper

    def reset_password(self):
        request = self.request
        request.matchdict = request.POST
        return super(AjaxForgotPasswordController, self).reset_password()


@view_auth_defaults
@view_config(attr='register', route_name='register', request_method='POST')
@view_config(attr='register_form', route_name='register', request_method='GET')
@view_config(attr='activate', route_name='activate', request_method='GET')
class RegisterController(object):
    def __init__(self, request):
        self.request = request
        self.schema = schemas.RegisterSchema().bind(request=self.request)
        self.form = deform.Form(self.schema)

    def register(self):
        """
        Handle submission of the new user registration form.

        Validates the form data, creates a new activation for the user, sends
        the activation mail, and then redirects the user to the index.
        """
        err, appstruct = validate_form(self.form, self.request.POST.items())
        if err is not None:
            return err

        # Create the new user from selected form fields
        props = {k: appstruct[k] for k in ['username', 'email', 'password']}
        user = User(**props)
        self.request.db.add(user)

        # Create a new activation for the user
        activation = Activation()
        self.request.db.add(activation)
        user.activation = activation

        # Flush the session to ensure that the user can be created and the
        # activation is successfully wired up
        self.request.db.flush()

        # Send the activation email
        message = activation_email(self.request, user)
        mailer = get_mailer(self.request)
        mailer.send(message)

        self.request.session.flash(_("Thank you for registering! Please check "
                                     "your e-mail now. You can continue by "
                                     "clicking the activation link we have "
                                     "sent you."),
                                   'success')
        self.request.registry.notify(RegistrationEvent(self.request, user))

        return httpexceptions.HTTPFound(
            location=self.request.route_url('index'))

    # FIXME: generate a form here and progressively enhance it rather than
    # relying entirely on Angular.
    def register_form(self):
        """Render the registration form."""
        # Logged in users shouldn't be able to register...
        if self.request.authenticated_userid is not None:
            return httpexceptions.HTTPFound(self.request.route_url('stream'))

        return {}

    def activate(self):
        """
        Handle a request for a user activation link.

        Checks if the activation code passed is valid, and (as a safety check)
        that it is an activation for the passed user id. If all is well,
        activate the user and redirect them to the stream.
        """
        code = self.request.matchdict.get('code')
        id_ = self.request.matchdict.get('id')

        if code is None or id_ is None:
            return httpexceptions.HTTPNotFound()

        try:
            id_ = int(id_)
        except ValueError:
            return httpexceptions.HTTPNotFound()

        activation = Activation.get_by_code(code)
        if activation is None:
            return httpexceptions.HTTPNotFound()

        user = User.get_by_activation(activation)
        if user is None or user.id != id_:
            return httpexceptions.HTTPNotFound()

        # Activate the user (by deleting the activation)
        self.request.db.delete(activation)

        self.request.session.flash(_("Your e-mail address has been verified. "
                                     "Thank you!"),
                                   'success')
        self.request.registry.notify(ActivationEvent(self.request, user))

        return httpexceptions.HTTPFound(
            location=self.request.route_url('index'))


@view_defaults(accept='application/json', context=Application, renderer='json')
@view_config(attr='register', request_param='__formid__=register')
@view_config(attr='activate', request_param='__formid__=activate')
class AjaxRegisterController(RegisterController):
    __view_mapper__ = AjaxFormViewMapper


@view_auth_defaults
@view_config(attr='edit_profile', route_name='edit_profile')
@view_config(attr='disable_user', route_name='disable_user')
@view_config(attr='profile', route_name='profile')
class ProfileController(object):
    def __init__(self, request):
        self.request = request
        self.schema = schemas.ProfileSchema().bind(request=self.request)
        self.form = deform.Form(self.schema)

    def edit_profile(self):
        """Handle POST payload from profile update form."""
        if self.request.method != 'POST':
            return httpexceptions.HTTPMethodNotAllowed()

        # Nothing to do here for non logged-in users
        if self.request.authenticated_userid is None:
            return httpexceptions.HTTPUnauthorized()

        err, appstruct = validate_form(self.form, self.request.POST.items())
        if err is not None:
            return err

        user = User.get_by_id(self.request.authenticated_userid)
        response = {'model': {'email': user.email}}

        # We allow updating subscriptions without validating a password
        subscriptions = appstruct.get('subscriptions')
        if subscriptions:
            data = json.loads(subscriptions)
            err = _update_subscription_data(self.request, data)
            if err is not None:
                return err
            return response

        # Any updates to fields below this point require password validation.
        #
        #   `pwd` is the current password
        #   `password` (used below) is optional, and is the new password
        #
        if not User.validate_user(user, appstruct.get('pwd')):
            return {'errors': {'pwd': _('Invalid password')}, 'code': 401}

        email = appstruct.get('email')
        if email:
            email_user = User.get_by_email(email)

            if email_user:
                if email_user.id != user.id:
                    return {
                        'errors': {'pwd': _('That email is already used')},
                    }

            response['model']['email'] = user.email = email

        password = appstruct.get('password')
        if password:
            user.password = password

        return response

    def disable_user(self):
        """Disable the user by setting a random password."""
        err, appstruct = validate_form(self.form, self.request.POST.items())
        if err is not None:
            return err

        username = appstruct['username']
        pwd = appstruct['pwd']

        # Password check
        user = User.get_user(username, pwd)
        if user:
            # TODO: maybe have an explicit disabled flag in the status
            user.password = User.generate_random_password()
            self.request.session.flash(_('Account disabled.'), 'success')
            return {}
        else:
            return dict(errors={'pwd': _('Invalid password')}, code=401)

    def profile(self):
        """
        Return a serialisation of the user's profile.

        For use by the frontend. Includes current email and subscriptions data.
        """
        request = self.request
        userid = request.authenticated_userid
        model = {}
        if userid:
            model["email"] = User.get_by_id(userid).email
        if request.feature('notification'):
            model['subscriptions'] = Subscriptions.get_subscriptions_for_uri(
                userid)
        return {'model': model}

    def unsubscribe(self):
        request = self.request
        subscription_id = request.GET['subscription_id']
        subscription = Subscriptions.get_by_id(subscription_id)
        if subscription:
            subscription.active = False
            return {}
        return {}


@view_defaults(accept='application/json', context=Application, renderer='json')
@view_config(attr='edit_profile', request_param='__formid__=edit_profile')
@view_config(attr='disable_user', request_param='__formid__=disable_user')
@view_config(attr='profile', request_param='__formid__=profile')
@view_config(attr='unsubscribe', request_param='__formid__=unsubscribe')
class AjaxProfileController(ProfileController):
    __view_mapper__ = AjaxFormViewMapper


def activation_email(request, user):
    """
    Generate an 'activate your account' email for the specified user.

    :rtype: pyramid_mailer.message.Message
    """
    link = request.route_url('activate', id=user.id, code=user.activation.code)

    emailtext = ("Please validate your email and activate your account by "
                 "visiting: {link}")
    body = emailtext.format(link=link)
    msg = Message(subject=_("Please activate your account"),
                  recipients=[user.email],
                  body=body)
    return msg


def reset_password_email(user, reset_code, reset_link):
    """
    Generate a 'reset your password' email for the specified user.

    :rtype: pyramid_mailer.message.Message
    """
    emailtext = ("Hello, {username}!\n\n"
                 "Someone requested resetting your password. If it was "
                 "you, reset your password by using this reset code:\n\n"
                 "{code}\n\n"
                 "Alternatively, you can reset your password by "
                 "clicking on this link:\n\n"
                 "{link}\n\n"
                 "If you don't want to change your password, please "
                 "ignore this email message.\n\n"
                 "Regards,\n"
                 "The Hypothesis Team\n")
    body = emailtext.format(code=reset_code,
                            link=reset_link,
                            username=user.username)
    msg = Message(subject=_("Reset your password"),
                  recipients=[user.email],
                  body=body)
    return msg


def reset_password_link(request, reset_code):
    """Transform an activation code into a password reset link."""
    return request.route_url('reset_password', code=reset_code)


def _update_subscription_data(request, subscription):
    """
    Update the subscriptions in the database from form data.

    Using data from the passed subscription struct, find a subscription in the
    database, and update it (if it belongs to the current logged-in user).
    """
    sub = Subscriptions.get_by_id(subscription['id'])
    if sub is None:
        return {
            'errors': {'subscriptions': _('Subscription not found')},
        }

    # If we're trying to update a subscription for anyone other than
    # the currently logged-in user, bail fast.
    #
    # The error message is deliberately identical to the one above, so
    # as not to leak any information about who which subscription ids
    # belong to.
    if sub.uri != request.authenticated_userid:
        return {
            'errors': {'subscriptions': _('Subscription not found')},
        }

    sub.active = subscription.get('active', True)

    request.session.flash(_('Changes saved!'), 'success')


def includeme(config):
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')
    config.add_route('register', '/register')
    config.add_route('activate', '/activate/{id}/{code}')
    config.add_route('profile', '/profile')
    config.add_route('edit_profile', '/profile/edit')
    config.add_route('forgot_password', '/forgot_password')
    config.add_route('reset_password', '/reset_password/{code}')
    config.add_route('disable_user', '/account/disable')
    config.scan(__name__)
