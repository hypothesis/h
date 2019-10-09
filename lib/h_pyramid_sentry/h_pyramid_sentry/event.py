"""
Decorator class for Sentry events.

Centralizes Sentry event parsing in one reusable place. Sentry events don't
have a very convenient interface in the form that sentry_sdk sends them to
us in.

They're dicts of dicts and tuples, and the structure changes depending on
whether the event is an exception raised or an error logged. This class
provides a more convenient interface to the interesting properties of events.
"""


class Event:
    """A decorator for a sentry_sdk event."""

    def __init__(self, event, hint):
        self._event = event
        self._hint = hint

    @property
    def event(self):
        """The raw event dict as passed to us by sentry_sdk."""
        return self._event

    @property
    def hint(self):
        """The raw hint dict as passed to us by sentry_sdk."""
        return self._hint

    @property
    def logger(self):
        """
        The name of the logger that logged the error message.

        A string, or None of this isn't a logger event.
        """
        return self.event.get("logger")

    @property
    def message(self):
        """
        The message that was logged.

        A string, or None of this isn't a logger event.
        """
        return self.event.get("logentry", {}).get("message")

    @property
    def exception(self):
        """
        The actual exception object that was raised.

        None if this isn't an exception event.
        """
        return self.hint.get("exc_info", (None, None, None))[1]
