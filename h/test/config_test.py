# -*- coding: utf-8 -*-

from h.config import configure


def test_configure_generates_secret_key_if_missing():
    config = configure(environ={}, settings={})

    assert 'secret_key' in config.registry.settings


def test_configure_doesnt_override_secret_key():
    config = configure(environ={}, settings={'secret_key': 'foobar'})

    assert config.registry.settings['secret_key'] == 'foobar'


def test_configure_generates_redis_sessions_secret_if_missing():
    config = configure(environ={}, settings={})

    assert 'redis.sessions.secret' in config.registry.settings


def test_missing_secrets_doesnt_override_redis_sessions_secret():
    config = configure(environ={}, settings={'redis.sessions.secret': 'isset'})

    assert config.registry.settings['redis.sessions.secret'] == 'isset'
