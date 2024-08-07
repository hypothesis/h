import pytest

from h.config import configure


@pytest.mark.parametrize(
    "env_var,env_val,setting_name,setting_val",
    [
        (None, None, "h.db_session_checks", True),
        ("DB_SESSION_CHECKS", "False", "h.db_session_checks", False),
        ("SECRET_KEY", "dont_tell_anyone", "secret_key", b"dont_tell_anyone"),
        ("SECRET_SALT", "best_with_pepper", "secret_salt", b"best_with_pepper"),
        ("SENTRY_ENVIRONMENT", "test-env", "h.sentry_environment", "test-env"),
        (
            "SENTRY_ENVIRONMENT",
            "test-env",
            "h_pyramid_sentry.init.environment",
            "test-env",
        ),
        # There are many other settings that can be updated from env vars.
        # These are not currently tested.
    ],
)
def test_configure_updates_settings_from_env_vars(
    env_var, env_val, setting_name, setting_val
):
    environ = {env_var: env_val} if env_var else {}
    settings_from_conf = {
        "h.db_session_checks": True,
        # Required settings
        "es.url": "https://es6-search-cluster",
        "secret_key": "notasecret",
        "h_api_auth_cookie_secret_key": b"test_h_api_auth_cookie_secret_key",
        "h_api_auth_cookie_salt": b"test_h_api_auth_cookie_salt",
        "sqlalchemy.url": "postgres://user@dbhost/dbname",
    }

    config = configure(environ=environ, settings=settings_from_conf)

    assert config.registry.settings[setting_name] == setting_val
