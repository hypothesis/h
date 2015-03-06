# -*- coding: utf-8 -*-
from mock import patch

from h import app


@patch('h.app.settings_from_environment')
def test_get_settings_env_overrides_base(settings_from_environment):
    base_settings = {'foo': 'base'}
    env_settings = {'foo': 'env'}

    settings_from_environment.return_value = env_settings
    result = app.get_settings({}, **base_settings)

    assert result['foo'] == 'env'


@patch('h.app.settings_from_environment')
def test_get_settings_global_overrides_all(settings_from_environment):
    base_settings = {'bar': 'base'}
    global_settings = {'bar': 'global'}
    env_settings = {'bar': 'env'}

    settings_from_environment.return_value = env_settings
    result = app.get_settings(global_settings, **base_settings)

    assert result['bar'] == 'global'


def test_missing_secrets_generates_secret_key():
    result = app.missing_secrets({})

    assert 'secret_key' in result
    assert 'redis.sessions.secret' in result


def test_missing_secrets_doesnt_override_secret_key():
    result = app.missing_secrets({'secret_key': 'foo'})

    assert 'secret_key' not in result
    assert 'redis.sessions.secret' in result


def test_missing_secrets_doesnt_override_redis_sesssions_secret():
    result = app.missing_secrets({'redis.sessions.secret': 'foo'})

    assert 'secret_key' in result
    assert 'redis.sessions.secret' not in result
