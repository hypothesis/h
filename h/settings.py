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

    def set(  # noqa: PLR0913
        self,
        name: str,
        envvar: str,
        type_=str,
        *,
        required: bool = False,
        default=None,
        deprecated_msg: str | None = None,
    ):
        """
        Update `setting[name]`.

        Update `setting[name]` using the value from the environment variable
        `envvar`. If there is no such environment variable and `setting[name]`
        is not already set, `setting[name]` is set to `default`.

        Raises `SettingError` if a required setting is missing and has no default,
        or coercing the setting using `type_` fails.

        :param name: the name of the pyramid config setting
        :param envvar: the environment variable name
        :param type_: callable that casts the setting value to the desired type
        :param required: True if the the pyramid config setting is required
        :param default: a default value to use if the envvar isn't set
        :param deprecated_msg: a deprecated envvar setting message to display
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
            raise SettingError(f"error parsing environment variable {envvar} not found")  # noqa: EM102, TRY003
        if val:
            try:
                self.settings[name] = type_(val)
            except ValueError as err:
                raise SettingError(  # noqa: TRY003
                    f"error casting {cast_message} as {type_.__name__}"  # noqa: EM102
                ) from err
