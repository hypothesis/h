from dataclasses import dataclass

from pyramid.request import Request

from h.models import User


@dataclass
class ActivationEvent:
    request: Request
    user: User


@dataclass
class LoginEvent:
    request: Request
    user: User


@dataclass
class LogoutEvent:
    request: Request


@dataclass
class PasswordResetEvent:
    request: Request
    user: User
