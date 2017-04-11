# -*- coding: utf-8 -*-

"""Helpers for parsing settings from the environment."""

from __future__ import unicode_literals

import logging

log = logging.getLogger(__name__)


class SettingError(Exception):
    pass


class DeprecatedSetting(object):
    """A wrapper for deprecated settings which emits appropriate warnings."""

    def __init__(self, setting, message):
        self.setting = setting
        self.message = message

        # Test seam
        self.warn = log.warn

    def __call__(self, environ):
        result = self.setting(environ)
        if result is not None:
            self.warn(self.warning)
        return result

    @property
    def warning(self):
        return 'use of {s} is deprecated: {m}'.format(s=self.setting,
                                                      m=self.message)


class EnvSetting(object):

    """An (optionally typed) setting read from an environment variable."""

    def __init__(self, setting, varname, type=None):
        self.setting = setting
        self.varname = varname
        if type is not None:
            self.type = type
        else:
            self.type = str

    def __call__(self, environ):
        if self.varname in environ:
            try:
                value = self.type(environ[self.varname])
            except ValueError:
                raise SettingError('error parsing environment variable '
                                   '{varname}={value!r} as {typename}'.format(
                                       varname=self.varname,
                                       typename=self.type.__name__,
                                       value=environ[self.varname]))
            return {self.setting: value}

    def __str__(self):
        return 'environment variable {name}'.format(name=self.varname)


def database_url(url):
    """Parse a string as a Heroku-style database URL."""
    # Heroku database URLs start with postgres://, which is an old and
    # deprecated dialect as far as sqlalchemy is concerned. We upgrade this
    # to postgresql+psycopg2 by default.
    if url.startswith('postgres://'):
        url = 'postgresql+psycopg2://' + url[len('postgres://'):]
    return url


def mandrill_settings(environ):
    if 'MANDRILL_USERNAME' in environ and 'MANDRILL_APIKEY' in environ:
        return {
            'mail.username': environ['MANDRILL_USERNAME'],
            'mail.password': environ['MANDRILL_APIKEY'],
            'mail.host': 'smtp.mandrillapp.com',
            'mail.port': 587,
            'mail.tls': True,
        }
