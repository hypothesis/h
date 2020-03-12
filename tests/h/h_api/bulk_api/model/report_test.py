import pytest

from h.h_api.bulk_api.model.report import Report
from h.h_api.enums import CommandResult


class TestReport:
    @pytest.mark.parametrize("outcome", [CommandResult.UPDATED, "updated"])
    def test_it(self, outcome):
        report = Report(outcome, "id")

        assert report.outcome == CommandResult.UPDATED
        assert report.id == "id"
