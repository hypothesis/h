from wtforms import PasswordField
from wtforms import TextField
from wtforms import validators

from pyramid.i18n import TranslationString as _

import apex.forms

from .. models import DBSession

class LoginForm(apex.forms.LoginForm):
    pass

class RegisterForm(apex.forms.RegisterForm):
    def after_signup(self, user):
        DBSession.flush()
