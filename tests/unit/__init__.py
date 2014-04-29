# -*- coding: utf-8 -*-
import os
from unittest import TestCase

from pyramid import paster


class AppTestCase(TestCase):

    """A subclass of unittest.TestCase for writing unit tests for h."""

    def setUp(self):
        paster.setup_logging('test.ini')
        self.settings = paster.get_appsettings('test.ini')
        self.settings.update({
            'basemodel.should_create_all': True,
            'basemodel.should_drop_all': True,
        })

        if os.environ.get('TRAVIS') == 'true':
            self.settings['es.compatibility'] = 'pre-1.0.0'
