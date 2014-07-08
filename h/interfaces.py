# -*- coding: utf-8 -*-
# pylint: disable=too-many-public-methods
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


class IStoreClass(Interface):
    pass


class IStreamResource(Interface):
    pass
