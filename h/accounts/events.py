class ActivationEvent:
    def __init__(self, request, user):  # pragma: no cover
        self.request = request
        self.user = user


class LoginEvent:
    def __init__(self, request, user):
        self.request = request
        self.user = user


class LogoutEvent:
    def __init__(self, request):
        self.request = request


class PasswordResetEvent:
    def __init__(self, request, user):
        self.request = request
        self.user = user
