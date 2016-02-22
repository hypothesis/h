# -*- coding: utf-8 -*-

import json
import unittest

import mock

from h.streamer import websocket


class TestWebSocket(unittest.TestCase):
    def setUp(self):
        fake_request = mock.MagicMock()
        fake_socket = mock.MagicMock()

        self.s = websocket.WebSocket(fake_socket)
        self.s.request = fake_request

    def test_filter_message_with_uri_gets_expanded(self):
        # FIXME: remove this when you remove the
        # 'ops_disable_streamer_uri_equivalence' feature.
        self.s.request.feature.return_value = False

        filter_message = json.dumps({
            'filter': {
                'actions': {},
                'match_policy': 'include_all',
                'clauses': [{
                    'field': '/uri',
                    'operator': 'equals',
                    'value': 'http://example.com',
                }],
            }
        })

        with mock.patch('h.api.storage.expand_uri') as expand_uri:
            expand_uri.return_value = ['http://example.com',
                                       'http://example.com/alter',
                                       'http://example.com/print']
            msg = mock.MagicMock()
            msg.data = filter_message

            self.s.received_message(msg)

            uri_filter = self.s.filter.filter['clauses'][0]
            uri_values = uri_filter['value']
            assert len(uri_values) == 3
            assert 'http://example.com' in uri_values
            assert 'http://example.com/alter' in uri_values
            assert 'http://example.com/print' in uri_values
