from __future__ import unicode_literals

import pytest
from mock import call
from webob.multidict import MultiDict

from h.util import metrics


class TestSendMetric(object):
    def test_send_metric(self, newrelic):
        metrics.send_metric("testkey", "testvalue")
        newrelic.agent.add_custom_parameter.assert_called_once_with(
            "testkey", "testvalue"
        )

    @pytest.fixture(autouse=True)
    def newrelic(self, patch):
        return patch("h.util.metrics.newrelic")


@pytest.mark.usefixtures("send_metric")
class TestRecordSearchApiUsageMetrics(object):
    def test_records_parameters(self, send_metric):
        params = MultiDict(tags="tagsvalue", url="urlvalue", bad="unwanted")
        metrics.record_search_api_usage_metrics(params)
        assert send_metric.call_args_list == [
            call("es_url", "urlvalue"),
            call("es_tags", "tagsvalue"),
        ]


@pytest.mark.usefixtures("send_metric")
class TestRecordSearchQueryParamUsage(object):
    def test_records_parameters(self, send_metric):
        params = MultiDict(tags="tagsvalue", url="urlvalue", bad="unwanted")
        metrics.record_search_query_param_usage(params, True)
        assert send_metric.call_args_list == [
            call("es__separate_replies", True),
            call("es_url", "urlvalue"),
            call("es_tags", "tagsvalue"),
        ]


@pytest.fixture
def send_metric(patch):
    return patch("h.util.metrics.send_metric")
