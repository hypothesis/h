from unittest import mock

import pytest

from h.models import Setting
from h.services.settings import SettingsService, settings_factory


class TestSettingsService:
    def test_get_returns_setting_value(self, factories, svc):
        # create one extra
        factories.Setting()
        setting = factories.Setting()

        assert svc.get(setting.key) == setting.value

    def test_get_returns_none_when_missing(self, svc):
        assert svc.get("missing") is None

    def test_put_creates_new_setting(self, db_session, svc):
        svc.put("custom-color", "red")

        setting = db_session.get(Setting, "custom-color")
        assert setting.key == "custom-color"
        assert setting.value == "red"

    def test_put_overrides_existing_setting(self, db_session, svc, factories):
        setting = factories.Setting()

        svc.put(setting.key, "green")

        setting = db_session.get(Setting, setting.key)
        assert setting.value == "green"

    def test_delete_deletes_existing_setting(self, db_session, svc, factories):
        setting = factories.Setting()

        svc.delete(setting.key)
        db_session.flush()

        assert db_session.get(Setting, setting.key) is None

    def test_delete_is_noop_when_setting_missing(self, svc, factories):
        # create a random setting
        factories.Setting()

        svc.delete("missing")


class TestSettingsFactory:
    def test_returns_service(self):
        svc = settings_factory(mock.Mock(), mock.Mock())

        assert isinstance(svc, SettingsService)

    def test_sets_session(self):
        request = mock.Mock()
        svc = settings_factory(mock.Mock(), request)

        assert svc.session == request.db


@pytest.fixture
def svc(db_session):
    return SettingsService(session=db_session)
