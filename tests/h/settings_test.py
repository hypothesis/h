# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from h import settings


@pytest.mark.parametrize('setting,varname,type,environ,expected', (
    # Should return None when the env var in question isn't set
    ('foo', 'FOO', None, {}, None),

    # Should return the setting as a string when the env var is set
    ('foo', 'FOO', None, {'FOO': 'bar'}, {'foo': 'bar'}),
    ('foo.bar', 'FOO', None, {'FOO': 'baz'}, {'foo.bar': 'baz'}),

    # Should coerce the result using the passed type
    ('foo', 'FOO', bytes, {'FOO': 'bar'}, {'foo': b'bar'}),
    ('app_port', 'PORT', int, {'PORT': '123'}, {'app_port': 123}),
))
def test_env_setting(setting, varname, type, environ, expected):
    func = settings.EnvSetting(setting, varname, type)

    result = func(environ)

    assert result == expected


def test_env_setting_returns_nicer_error_for_type_failure():
    func = settings.EnvSetting('port', 'PORT', type=int)

    with pytest.raises(settings.SettingError):
        func({'PORT': 'notanint'})


@pytest.mark.parametrize('setting,link,pattern,environ,expected', (
    # Should return None if any of the required vars aren't set
    ('database_url', 'db', 'db://{addr}', {}, None),
    ('database_url', 'db', 'db://{addr}', {'DB_HOST': 'foo'}, None),
    ('database_url', 'db', 'db://{host}:{port}', {'DB_ADDR': 'foo'}, None),

    # Should return the settings object if all of the parts are available
    ('database_url', 'db', 'db://{addr}',
     {'DB_ADDR': 'foo'},
     {'database_url': 'db://foo'}),
    ('database_url', 'db', 'db://{host}:{port}',
     {'DB_HOST': 'foo', 'DB_PORT': '123'},
     {'database_url': 'db://foo:123'}),
))
def test_docker_setting(setting, link, pattern, environ, expected):
    func = settings.DockerSetting(setting, link, pattern)

    result = func(environ)

    assert result == expected


def test_database_url():
    url = 'postgres://postgres:1234/database'
    expected = 'postgresql+psycopg2://postgres:1234/database'

    assert settings.database_url(url) == expected


def test_mandrill_settings():
    environ = {
        'MANDRILL_USERNAME': 'foobar',
        'MANDRILL_APIKEY': 'wibble',
    }
    expected = {
        'mail.username': 'foobar',
        'mail.password': 'wibble',
        'mail.host': 'smtp.mandrillapp.com',
        'mail.port': 587,
        'mail.tls': True,
    }

    assert settings.mandrill_settings(environ) == expected


def test_mandrill_settings_unset():
    assert settings.mandrill_settings({}) is None
