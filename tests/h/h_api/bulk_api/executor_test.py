from unittest.mock import sentinel

import pytest
from h_matchers import Any

from h.h_api.bulk_api.executor import AutomaticReportExecutor
from h.h_api.bulk_api.model.report import Report
from h.h_api.enums import CommandType


class TestAutomaticReportExecutor:
    @pytest.mark.parametrize(
        "command_type", (CommandType.CREATE, CommandType.UPSERT),
    )
    def test_execute_batch_returns_an_appropriate_type(self, command_type):
        results = AutomaticReportExecutor().execute_batch(
            command_type, sentinel.data_type, sentinel.config, batch=[sentinel.command]
        )

        assert results == [Any.instance_of(Report)]

    def test_execute_batch_generates_fake_ids(self):
        results = AutomaticReportExecutor().execute_batch(
            sentinel.command_type,
            sentinel.data_type,
            sentinel.config,
            batch=[sentinel.command, sentinel.command, sentinel.command],
        )

        assert results == Any.list.comprised_of(Any.instance_of(Report)).of_size(3)
        assert len({report.id for report in results}) == 3
