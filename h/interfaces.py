# -*- coding: utf-8 -*-
# pylint: disable=too-many-public-methods
from hem.interfaces import IDBSession

from horus.interfaces import (
    IUserClass,
    IActivationClass,

    ILoginForm,
    IRegisterForm,
    IForgotPasswordForm,
    IResetPasswordForm,
    IProfileForm,

    ILoginSchema,
    IRegisterSchema,
    IForgotPasswordSchema,
    IResetPasswordSchema,
    IProfileSchema,

    IUIStrings,
)

from zope.interface import Interface

__all__ = [
    'IDBSession',
    'IUIStrings',

    'IUserClass',
    'IActivationClass',
    'IAnnotationClass',

    'ILoginForm',
    'IRegisterForm',
    'IForgotPasswordForm',
    'IResetPasswordForm',
    'IProfileForm',

    'ILoginSchema',
    'IRegisterSchema',
    'IForgotPasswordSchema',
    'IResetPasswordSchema',
    'IProfileSchema',
]


class IAnnotationClass(Interface):
    pass


class IConsumerClass(Interface):
    pass


class IStoreClass(Interface):
    pass


class IActivateForm(Interface):
    pass


class IActivateSchema(Interface):
    pass


class IStreamResource(Interface):
    pass
