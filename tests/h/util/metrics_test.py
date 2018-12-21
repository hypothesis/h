from __future__ import unicode_literals

import pytest
import mock
from webob.multidict import MultiDict

from h.util import metrics


class TestRecordSearchQueryParams(object):
    def test_records_parameters(self, newrelic_agent):
        params = MultiDict(tag="tagsvalue",
                           _separate_replies=True,
                           url="urlvalue",
                           bad="unwanted")
        metrics.record_search_query_params(params)
        newrelic_agent.current_transaction().add_custom_parameters.assert_called_once_with(
            [("es_url", "urlvalue"),
             ("es_tag", "tagsvalue"),
             ("es__separate_replies", True)])

    def test_does_not_record_parameters_if_no_transaction(self, newrelic_agent):
        newrelic_agent.current_transaction.return_value = None
        params = MultiDict(tag="tagsvalue",
                           _separate_replies=True,
                           url="urlvalue",
                           bad="unwanted")
        metrics.record_search_query_params(params)

    @pytest.fixture
    def newrelic_agent(self, newrelic_agent):
        newrelic_agent.current_transaction.return_value.add_custom_parameters = mock.Mock()
        return newrelic_agent


@pytest.fixture
def newrelic_agent(patch):
    return patch("h.util.metrics.newrelic.agent")
