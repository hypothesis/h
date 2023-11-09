import logging

import pytest

from h.settings import SettingError, SettingsManager, database_url


def test_database_url():
    url = "postgres://postgres:1234/database"
    expected = "postgresql+psycopg2://postgres:1234/database"

    assert database_url(url) == expected


class TestSettingsManager:
    def test_set_does_not_warn_when_deprecated_setting_is_not_used(self, caplog):
        with caplog.at_level(logging.WARN):
            settings_manager = SettingsManager({}, {})
            settings_manager.set("foo", "FOO", deprecated_msg="what to do instead")
        assert not caplog.records

    def test_set_sets_value_when_deprecated_setting_is_used(self):
        settings_manager = SettingsManager(environ={"FOO": "bar"})
        settings_manager.set("foo", "FOO", deprecated_msg="what to do instead")

        result = settings_manager.settings["foo"]

        assert result == "bar"

    def test_set_warns_when_deprecated_setting_is_used(self, caplog):
        with caplog.at_level(logging.WARN):
            settings_manager = SettingsManager({}, {"FOO": "bar"})
            settings_manager.set("foo", "FOO", deprecated_msg="what to do instead")
        assert "what to do instead" in caplog.text

    def test_set_uses_config_var_if_env_var_not_set(self):
        settings_manager = SettingsManager(settings={"foo": None}, environ={})
        settings_manager.set("foo", "FOO")
        assert settings_manager.settings["foo"] is None

    def test_set_coerces_value_to_specified_type(self):
        environ = {"PORT": "123"}
        settings_manager = SettingsManager(settings={"port": None}, environ=environ)

        settings_manager.set("port", "PORT", type_=int)

        assert settings_manager.settings["port"] == 123

    def test_set_uses_default(self):
        settings_manager = SettingsManager(settings={}, environ={})
        settings_manager.set("port", "PORT", default=123, type_=int)
        assert settings_manager.settings["port"] == 123

    def test_set_prefers_env_var_to_default(self):
        environ = {"PORT": "123"}
        settings_manager = SettingsManager(settings={"port": None}, environ=environ)

        settings_manager.set("port", "PORT", default=456, type_=int)

        assert settings_manager.settings["port"] == 123

    def test_set_prefers_env_var_to_config(self):
        environ = {"PORT": "123"}
        settings_manager = SettingsManager(settings={"port": "456"}, environ=environ)

        settings_manager.set("port", "PORT", type_=int)

        assert settings_manager.settings["port"] == 123

    def test_set_prefers_config_var_to_default(self):
        settings_manager = SettingsManager(settings={"port": 123}, environ={})
        settings_manager.set("port", "PORT", default=456, type_=int)
        assert settings_manager.settings["port"] == 123

    def test_set_does_not_error_if_required_but_default_provided(self):
        settings_manager = SettingsManager(settings={}, environ={})
        settings_manager.set("port", "PORT", default=123, required=True, type_=int)
        assert settings_manager.settings["port"] == 123

    @pytest.mark.parametrize(
        "name,envvar,type_,environ,default",
        (
            # Should raise because default isn't an int
            ("foo", "FOO", int, {}, "notanint"),
            # Should raise because environment variable isn't an int
            ("foo", "FOO", int, {"FOO": "notanint"}, None),
        ),
    )
    def test_raises_when_unable_to_type_cast(
        self, name, envvar, type_, environ, default
    ):
        settings_manager = SettingsManager(environ=environ)
        with pytest.raises(SettingError):
            settings_manager.set(name, envvar, type_=type_, default=default)

    def test_raises_when_required_and_missing_from_all_sources(self):
        settings_manager = SettingsManager({"bar": "val"}, {"BAR": "bar"})
        with pytest.raises(SettingError):
            settings_manager.set("foo", "FOO", required=True)

    def test_defaults_settings_to_empty_dict(self):
        settings_manager = SettingsManager()
        assert not settings_manager.settings

    @pytest.mark.usefixtures("environ")
    def test_defaults_environ_to_osenviron(self):
        settings_manager = SettingsManager()
        settings_manager.set("foo", "FOO", default="bar")
        result = settings_manager.settings["foo"]
        assert result == "foo"

    def test_it_preserves_extra_config_settings(self):
        settings_manager = SettingsManager({"pyramid.setting": True})
        assert settings_manager.settings["pyramid.setting"] is True

    @pytest.fixture
    def environ(self, patch):
        patched_os = patch("h.settings.os")
        patched_os.environ = {"FOO": "foo"}
        return patched_os
