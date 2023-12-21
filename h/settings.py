"""Helpers for parsing settings from the environment."""

import logging
import os

log = logging.getLogger(__name__)


class SettingError(Exception):
    """Exception thrown when a setting cannot be resolved."""


class SettingsManager:
    """
    Configuration setting resolver.

    SettingsManager resolves settings from various sources into the final typed
    values used when the app runs. It also provides a way to check for missing
    required settings or use of deprecated settings.

    The resolved settings are available via the `settings` attribute.
    """

    def __init__(self, settings=None, environ=None):
        """
        Initialize with initial setting values from config files and environment.

        :param settings: Initial configuration settings read from config files
        :type settings: Dict[str,str]
        :param environ: Environment variable mappings
        :type environ: Dict[str, str]
        """
        if environ is None:
            environ = os.environ

        self.settings = {}
        self.settings.update(settings or {})

        self._environ = environ

    def set(  # pylint: disable=too-many-arguments
        self,
        name,
        envvar,
        type_=str,
        required=False,
        default=None,
        deprecated_msg=None,
    ):
        """
        Update `setting[name]`.

        Update `setting[name]` using the value from the environment variable
        `envvar`. If there is no such environment variable and `setting[name]`
        is not already set, `setting[name]` is set to `default`.

        Raises `SettingError` if a required setting is missing and has no default,
        or coercing the setting using `type_` fails.

        :param name: the name of the pyramid config setting
        :type name: str
        :param envvar: the environment variable name
        :type envvar: str
        :param type_: callable that casts the setting value to the desired type
        :param required: True if the the pyramid config setting is required
        :type required: bool
        :param default: a default value to use if the envvar isn't set
        :param deprecated_msg: a deprecated envvar setting message to display
        :type deprecated_msg: str
        :raises SettingError: if required and not set
        :raises SettingError: if type casting fails
        """
        val = None
        cast_message = None
        if envvar in self._environ:
            if deprecated_msg:
                log.warning(
                    "use of envvar %s is deprecated: %s", envvar, deprecated_msg
                )
            val = self._environ[envvar]
            cast_message = f"environment variable {envvar}={val!r}"
        elif default and name not in self.settings:
            val = default
            cast_message = f"{name}'s default {val!r}"
        elif required and name not in self.settings:
            raise SettingError(f"error parsing environment variable {envvar} not found")
        if val:
            try:
                self.settings[name] = type_(val)
            except ValueError as err:
                raise SettingError(
                    f"error casting {cast_message} as {type_.__name__}"
                ) from err


def database_url(url):
    """Parse a string as a Heroku-style database URL."""
    # Heroku database URLs start with postgres://, which is an old and
    # deprecated dialect as far as sqlalchemy is concerned. We upgrade this
    # to postgresql+psycopg2 by default.
    if url.startswith("postgres://"):
        url = "postgresql+psycopg2://" + url[len("postgres://") :]
    return url
