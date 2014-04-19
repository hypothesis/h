# -*- coding: utf-8 -*-
import deform

from h import interfaces


class Deform(deform.Form):
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
