from webob.cookies import SignedCookieProfile


class AuthCookie:
    """An authentication source that uses a unique cookie."""

    vary = ["Cookie"]

    def __init__(self, request):
        cookie = SignedCookieProfile(
            secret=request.registry.settings["h_auth_cookie_secret"],
            salt="authsanity",
            cookie_name="auth",
            secure=False,
            max_age=2592000,
            httponly=True,
        )

        # Bind the cookie to the current request
        self.cookie = cookie.bind(request)

    def get_value(self):
        val = self.cookie.get_value()

        if val is None:
            return [None, None]

        return val

    def headers_remember(self, value):
        return self.cookie.get_headers(value)

    def headers_forget(self):
        return self.cookie.get_headers(None, max_age=0)
