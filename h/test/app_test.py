# -*- coding: utf-8 -*-
from mock import patch

from h import app, config


@patch('h.config.settings_from_environment')
@patch('h.app.create_app')
def test_global_settings_precedence(create_app, settings_from_environment):
    base_settings = {
        'foo': 'bar',
    }
    env_settings = {
        'foo': 'override',
        'booz': 'baz',
    }
    global_settings = {
        'booz': 'override',
    }

    settings_from_environment.return_value = env_settings
    app.main(global_settings, **base_settings)
    assert config.settings_from_environment.call_count == 1

    args, kwargs = app.create_app.call_args
    result = args[0]
    assert result['foo'] == 'override'
    assert result['booz'] == 'override'


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
