# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from h.sentry import get_client


class TestGetClient(object):
    @pytest.mark.parametrize(
        "settings,env",
        [({}, "dev"), ({"h.env": "qa"}, "qa"), ({"h.env": "prod"}, "prod")],
    )
    def test_set_environment(self, settings, env):
        client = get_client(settings)

        assert client.environment == env
