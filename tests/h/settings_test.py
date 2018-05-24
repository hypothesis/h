# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest
import logging

from h.settings import (SettingsManager,
                        SettingError,
                        database_url)


def asutf8(string):
    return string.encode()


def test_database_url():
    url = 'postgres://postgres:1234/database'
    expected = 'postgresql+psycopg2://postgres:1234/database'

    assert database_url(url) == expected


class TestSettingsManager(object):
    def test_does_not_warn_when_deprecated_setting_is_not_used(self, caplog):
        with caplog.at_level(logging.WARN):
            settings_manager = SettingsManager({}, {})
            settings_manager.set('foo', 'FOO', deprecated_msg='what to do instead')
        assert not caplog.records

    def test_sets_value_when_deprecated_setting_is_used(self):
        settings_manager = SettingsManager(environ={'FOO': 'bar'})
        settings_manager.set('foo', 'FOO', deprecated_msg='what to do instead')

        result = settings_manager.settings['foo']

        assert result == 'bar'

    def test_warns_when_deprecated_setting_is_used(self, caplog):
        with caplog.at_level(logging.WARN):
            settings_manager = SettingsManager({}, {'FOO': 'bar'})
            settings_manager.set('foo', 'FOO', deprecated_msg='what to do instead')
        assert 'what to do instead' in caplog.text

    @pytest.mark.parametrize('settings,name,envvar,type_,environ,required,default,expected', (
        # Should leave value at None when the env var in question isn't set
        ({'foo': None}, 'foo', 'FOO', str, {}, False, None, None),

        # Should return the setting as a string when the env var is set
        ({}, 'foo', 'FOO', str, {'FOO': 'bar'}, False, None, 'bar'),
        ({'foo.bar': 'foo.bar'}, 'foo.bar', 'FOO', str, {'FOO': 'baz'}, False, None, 'baz'),

        # Should coerce the result using the passed type
        ({}, 'foo', 'FOO', asutf8, {'FOO': 'bar'}, False, None, asutf8('bar')),
        ({}, 'app_port', 'PORT', int, {'PORT': '123'}, False, None, 123),

        # Should overide the value when a default is provided
        ({}, 'bar', 'BAR', str, {}, True, 'bar', 'bar'),

        # Should not overide the value when a default is provided and the envvar is set
        ({}, 'foo', 'FOO', str, {'FOO': 'bar'}, True, 'boo', 'bar'),

        # Should not error when required and a default is already set
        ({'foo': 'foo'}, 'foo', 'FOO', str, {}, True, None, 'foo'),

        # Should not overide default if default is already set
        ({'boo': 'boo'}, 'boo', 'BOO', str, {}, True, 'foo', 'boo'),

    ))
    def test_env_setting(self, settings, name, envvar, type_, environ, required, default, expected):
        settings_manager = SettingsManager(settings, environ)
        settings_manager.set(name, envvar, type_, required, default)

        result = settings[name]

        assert result == expected

    @pytest.mark.parametrize('name,envvar,type_,environ,default', (
        # Should raise because default isn't an int
        ('foo', 'FOO', int, {}, 'notanint'),
        # Should raise because environment variable isn't an int
        ('foo', 'FOO', int, {'FOO': 'notanint'}, None),
        ))
    def test_raises_when_unable_to_type_cast(self, name, envvar, type_, environ, default):
        settings_manager = SettingsManager(environ=environ)
        with pytest.raises(SettingError):
            settings_manager.set(name, envvar, type_=type_, default=default)

    def test_raises_when_not_in_env_no_default_and_required(self):
        settings_manager = SettingsManager({'bar': 'val'}, {'BAR': 'bar'})
        with pytest.raises(SettingError):
            settings_manager.set('foo', 'FOO', required=True)

    def test_defaults_settings_to_empty_dict(self):
        settings_manager = SettingsManager()
        assert settings_manager.settings == {}

    def test_defaults_environ_to_osenviron(self, environ):
        settings_manager = SettingsManager()
        settings_manager.set('foo', 'FOO', default='bar')
        result = settings_manager.settings['foo']
        assert result == 'foo'

    @pytest.fixture
    def environ(self, patch):
        patched_os = patch('h.settings.os')
        patched_os.environ = {'FOO': 'foo'}
        return patched_os
