# -*- coding: utf-8 -*-
from mock import call, patch

from h import app, config


@patch('h.config.settings_from_environment')
@patch('h.app.create_app')
def test_global_config_precence(create_app, settings_from_environment):
    base_config = {
        'foo': 'bar',
    }
    env_config = {
        'foo': 'override',
        'booz': 'baz',
    }
    global_config = {
        'booz': 'override',
    }
    expected_config = {
        'foo': 'override',
        'booz': 'override',
    }

    settings_from_environment.return_value = env_config
    app.main(global_config, **base_config)
    assert config.settings_from_environment.call_count == 1
    assert app.create_app.mock_calls == [call(expected_config)]
