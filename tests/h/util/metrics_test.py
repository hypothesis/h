from __future__ import unicode_literals

import pytest
import mock
from webob.multidict import MultiDict

from h.util import metrics


class TestRecordSearchQueryParams(object):
    def test_it_passes_parameters_to_newrelic(self, newrelic_agent):
        params = MultiDict(tag="tagsvalue", _separate_replies=True, url="urlvalue")
        metrics.record_search_query_params(params, True)
        newrelic_agent.current_transaction().add_custom_parameters.assert_called_once_with(
            [
                ("es_url", "urlvalue"),
                ("es_tag", "tagsvalue"),
                ("es__separate_replies", True),
            ]
        )

    def test_it_does_not_pass_unrecognized_parameters_to_newrelic(self, newrelic_agent):
        params = MultiDict(bad="unwanted")
        metrics.record_search_query_params(params, True)
        newrelic_agent.current_transaction().add_custom_parameters.assert_called_once_with(
            [("es__separate_replies", True)]
        )

    def test_it_does_not_record_separate_replies_if_False(self, newrelic_agent):
        params = MultiDict({})
        metrics.record_search_query_params(params, False)
        newrelic_agent.current_transaction().add_custom_parameters.assert_called_once_with(
            []
        )

    def test_it_does_not_record_parameters_if_no_transaction(self, newrelic_agent):
        newrelic_agent.current_transaction.return_value = None
        params = MultiDict(tag="tagsvalue")
        metrics.record_search_query_params(params, True)

    @pytest.fixture
    def newrelic_agent(self, newrelic_agent):
        newrelic_agent.current_transaction.return_value.add_custom_parameters = (
            mock.Mock()
        )
        return newrelic_agent


@pytest.fixture
def newrelic_agent(patch):
    return patch("h.util.metrics.newrelic.agent")
