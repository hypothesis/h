# -*- coding: utf-8 -*-
# pylint: disable=too-many-public-methods
import deform

from horus import interfaces
from zope.interface import Interface


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
    registry = config.registry

    forms = [
        (interfaces.ILoginForm, LoginForm),
        (interfaces.IRegisterForm, RegisterForm),
        (interfaces.IForgotPasswordForm, ForgotForm),
        (interfaces.IResetPasswordForm, ResetForm),
    ]

    for iface, imp in forms:
        if not registry.queryUtility(iface):
            registry.registerUtility(imp, iface)
