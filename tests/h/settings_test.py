# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest
import mock

from h import settings


class FakeSetting(object):
    def __init__(self, result):
        self.result = result

    def __call__(self, environ):
        return self.result

    def __str__(self):
        return 'fake setting'


class TestDeprecatedSetting(object):
    def test_emits_warnings_when_child_setting_is_used(self):
        func = settings.DeprecatedSetting(FakeSetting(result={'foo': 'bar'}),
                                          message='what to do instead')
        func.warn = mock.Mock(spec_set=[])

        result = func({})

        assert result == {'foo': 'bar'}
        func.warn.assert_called_once_with('use of fake setting is '
                                          'deprecated: what to do instead')

    def test_emits_no_warnings_when_unused(self):
        func = settings.DeprecatedSetting(FakeSetting(result=None),
                                          message='what to do instead')
        func.warn = mock.Mock(spec_set=[])

        result = func({})

        assert result is None
        assert not func.warn.called


def asutf8(str):
    return str.encode()


@pytest.mark.parametrize('setting,varname,type,environ,expected', (
    # Should return None when the env var in question isn't set
    ('foo', 'FOO', None, {}, None),

    # Should return the setting as a string when the env var is set
    ('foo', 'FOO', None, {'FOO': 'bar'}, {'foo': 'bar'}),
    ('foo.bar', 'FOO', None, {'FOO': 'baz'}, {'foo.bar': 'baz'}),

    # Should coerce the result using the passed type
    ('foo', 'FOO', asutf8, {'FOO': 'bar'}, {'foo': b'bar'}),
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
