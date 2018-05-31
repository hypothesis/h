# -*- coding: utf-8 -*-

"""Helpers for parsing settings from the environment."""

from __future__ import unicode_literals

import logging
import os

log = logging.getLogger(__name__)


class SettingError(Exception):
    pass


class SettingsManager(object):
    """
    Configuration setting resolver.

    SettingsManager resolves settings from various sources into the final typed
    values used when the app runs. It also provides a way to check for missing
    required settings or use of deprecated settings.

    The resolved settings are available via the `settings` attribute.
    """

    def __init__(self, settings=None, environ=None):
        """
        Initialize SettingsManager with initial setting values from config files
        and the environment.

        :param settings: Initial configuration settings read from config files
        :type settings: Dict[str,str]
        :param environ: Environment variable mappings
        :type environ: Dict[str, str]
        """

        if settings is None:
            settings = {}
        if environ is None:
            environ = os.environ
        self.settings = settings
        self._environ = environ

    def set(self,  # pylint: disable=too-many-arguments
            name,
            envvar,
            type_=str,
            required=False,
            default=None,
            deprecated_msg=None):
        """
        Resolve a typed value for a setting.

        Sets the setting `name` to the value from the highest priority source
        and coerces the result to a typed value using `type_`. The sources
        in priority order are: 1) Environment variables (`envvar`), 2)
        Configuration files (passed to the constructor), 3) Defaults (`default`).

        If `required` is `True` then an error is raised if no source specifies
        a value for this setting.

        :param name: the name of the pyramid config setting
        :type name: str
        :param envvar: the environment variable name
        :type envvar: str
        :param type_: callable that casts a string to the desired type
        :param required: True if the the pyramid config setting is required
        :type required: bool
        :param default: a default value to use if the envvar isn't set
        :param deprecated_msg: a deprecated envvar setting message to display
        :type deprecated_msg: str
        :raises SettingsError: if required and not set
        :raises SettingsError: if type casting fails
        """
        val = None
        cast_message = None
        if envvar in self._environ:
            if deprecated_msg:
                log.warn('use of envvar %s is deprecated: %s',
                         envvar,
                         deprecated_msg)
            val = self._environ[envvar]
            cast_message = "environment variable {}={!r}".format(envvar, val)
        elif default and name not in self.settings:
            val = default
            cast_message = "{}'s default {!r}".format(name, val)
        elif required and name not in self.settings:
            raise SettingError(
                'error parsing environment variable '
                '{varname} not found'.format(varname=envvar))
        if val:
            try:
                self.settings[name] = type_(val)
            except ValueError:
                raise SettingError('error casting {} as {}'.format(
                                       cast_message,
                                       type_.__name__))


def database_url(url):
    """Parse a string as a Heroku-style database URL."""
    # Heroku database URLs start with postgres://, which is an old and
    # deprecated dialect as far as sqlalchemy is concerned. We upgrade this
    # to postgresql+psycopg2 by default.
    if url.startswith('postgres://'):
        url = 'postgresql+psycopg2://' + url[len('postgres://'):]
    return url
