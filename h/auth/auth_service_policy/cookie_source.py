from webob.cookies import SignedCookieProfile


class CookieAuthService:
    """An authentication source that uses a unique cookie."""

    vary = ["Cookie"]

    def __init__(self, request, secret):
        cookie = SignedCookieProfile(
            secret=secret,
            salt="authsanity",
            cookie_name="auth",
            secure=False,
            max_age=2592000,
            httponly=True,
            path="/",
            domains=[],
            hashalg="sha512",
        )

        self.cookie = cookie.bind(request)

    def get_value(self):
        val = self.cookie.get_value()

        if val is None:
            return [None, None]

        return val

    def headers_remember(self, value):
        return self.cookie.get_headers(value, domains=self.cookie.domains)

    def headers_forget(self):
        return self.cookie.get_headers(None, max_age=0)


def factory_factory(secret):
    def factory(context, request):
        # Bind the cookie to the current request
        return CookieAuthService(request, secret)

    return factory
