__all__ = [
    'IUserClass',
    'IActivationClass',

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

from zope.interface import Interface

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
)


class IActivateForm(Interface):
    pass


class IActivateSchema(Interface):
    pass
