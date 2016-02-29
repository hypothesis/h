# -*- coding: utf-8 -*-

"""Helpers for parsing settings from the environment."""

import string


class SettingError(Exception):
    pass


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


class DockerSetting(object):

    """A setting read from Docker link environment variables."""

    def __init__(self, setting, link, pattern):
        self.setting = setting
        self.link = link.upper()
        self.pattern = pattern

        # Determine the settings that need to be present
        formatter = string.Formatter()
        self.placeholders = [field
                             for _, field, _, _ in formatter.parse(pattern)
                             if field is not None]

    def __call__(self, environ):
        try:
            values = {x: environ['{}_{}'.format(self.link, x.upper())]
                      for x in self.placeholders}
        except KeyError:
            pass
        else:
            return {self.setting: self.pattern.format(**values)}


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
