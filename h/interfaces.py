__all__ = [
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

    IUIStrings,
)


class IAnnotationClass(Interface):
    pass


class IConsumerClass(Interface):
    pass


class IStoreClass(Interface):
    pass


class ITokenClass(Interface):
    pass


class IActivateForm(Interface):
    pass


class IActivateSchema(Interface):
    pass
