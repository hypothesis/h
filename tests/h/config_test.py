# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import pytest

from h.config import configure


def test_configure_generates_secret_key_if_missing():
    config = configure(environ={}, settings={})

    assert 'secret_key' in config.registry.settings


def test_configure_doesnt_override_secret_key():
    config = configure(environ={}, settings={'secret_key': 'foobar'})

    assert config.registry.settings['secret_key'] == 'foobar'


@pytest.mark.parametrize('env_var,env_val,setting_name,setting_val', [
    (None, None, 'h.db_session_checks', True),
    ('DB_SESSION_CHECKS', "False", 'h.db_session_checks', False),

    # There are many other settings that can be updated from env vars.
    # These are not currently tested.
])
def test_configure_updates_settings_from_env_vars(env_var, env_val, setting_name, setting_val):
    environ = {env_var: env_val} if env_var else {}
    settings_from_conf = {'h.db_session_checks': True}

    config = configure(environ=environ, settings=settings_from_conf)

    assert config.registry.settings[setting_name] == setting_val
