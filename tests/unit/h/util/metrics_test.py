from unittest import mock

import pytest
from webob.multidict import MultiDict

from h.util import metrics


class TestRecordSearchQueryParams:
    def test_it_passes_parameters_to_newrelic(self, newrelic_agent):
        params = MultiDict(tag="tagsvalue", _separate_replies=True, url="urlvalue")
        metrics.record_search_query_params(params, True)
        newrelic_agent.add_custom_attributes.assert_called_once_with(
            [
                ("es_url", "urlvalue"),
                ("es_tag", "tagsvalue"),
                ("es__separate_replies", True),
            ]
        )

    def test_it_does_not_pass_unrecognized_parameters_to_newrelic(self, newrelic_agent):
        params = MultiDict(bad="unwanted")
        metrics.record_search_query_params(params, True)
        newrelic_agent.add_custom_attributes.assert_called_once_with(
            [("es__separate_replies", True)]
        )

    def test_it_does_not_record_separate_replies_if_False(self, newrelic_agent):
        params = MultiDict({})
        metrics.record_search_query_params(params, False)
        newrelic_agent.add_custom_attributes.assert_called_once_with([])

    @pytest.fixture
    def newrelic_agent(self, newrelic_agent):
        newrelic_agent.add_custom_attributes = mock.Mock()
        return newrelic_agent


@pytest.fixture
def newrelic_agent(patch):
    return patch("h.util.metrics.newrelic.agent")
