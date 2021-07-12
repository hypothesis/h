from h.models import Setting


class SettingsService:
    """A service for fetching and manipulating settings."""

    def __init__(self, session):
        """
        Create a new settings service.

        :param session: the SQLAlchemy session object
        """
        self.session = session

    def get(self, key):
        setting = self._fetch(key)

        if setting is None:
            return None

        return setting.value

    def put(self, key, value):
        setting = self._fetch(key)

        if setting is None:
            setting = Setting(key=key)

        setting.value = value
        self.session.add(setting)

    def delete(self, key):
        setting = self._fetch(key)

        if setting is not None:
            self.session.delete(setting)

    def _fetch(self, key):
        return self.session.query(Setting).get(key)


def settings_factory(_context, request):
    """Return a SettingsService instance for the passed context and request."""
    return SettingsService(session=request.db)
