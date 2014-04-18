# -*- coding: utf-8 -*-
import re

import deform

from h import interfaces


class FormMeta(type):
    def __new__(cls, name, bases, attrs):
        """Constructs a new Form class."""
        # Convert to the class name to a form id.
        # Names like 'CamelCaseNameForm' will become 'camel-case-name'.
        formid = name.replace('Form', '')
        formid = (
            formid[0].lower() +
            re.sub(r'([A-Z])', lambda m: "-" + m.group(0).lower(), formid[1:])
        )
        attrs.setdefault('formid', formid)
        return type.__new__(cls, name, bases, attrs)


class Deform(deform.Form):
    __metaclass__ = FormMeta
    buttons = (deform.Button('submit'),)

    def __init__(self, schema, **kwargs):
        kwargs.setdefault('buttons', self.buttons)
        super(Deform, self).__init__(schema, **kwargs)


class LoginForm(Deform):
    buttons = (deform.Button('Sign in'),)


class RegisterForm(Deform):
    buttons = (deform.Button('Register'),)


class ForgotForm(Deform):
    buttons = (deform.Button('Send code'),)


class ResetForm(Deform):
    buttons = (deform.Button('Reset password'),)


class ActivateForm(Deform):
    buttons = (deform.Button('Sign in'),)


def includeme(config):
    forms = [
        (interfaces.ILoginForm, LoginForm),
        (interfaces.IRegisterForm, RegisterForm),
        (interfaces.IForgotPasswordForm, ForgotForm),
        (interfaces.IResetPasswordForm, ResetForm),
        (interfaces.IActivateForm, ActivateForm)
    ]

    for iface, imp in forms:
        if not config.registry.queryUtility(iface):
            config.registry.registerUtility(imp, iface)
