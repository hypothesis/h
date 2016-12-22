# -*- coding: utf-8 -*-

"""
An example of using :py:package:`memex` to run a standalone annotation API.

This is a small example web application, demonstrating how to use the
:py:package:`memex` package to serve a Hypothesis-like annotation API. In this
example, the list of users is defined in a constant at the top of the
``auth.py`` file. In a more conventional setting, developers are expected to
integrate their accounts system with the web application by way of a Pyramid
Authentication Policy.

The users defined in the USERS constant at the top of the ``auth.py`` file can
make requests to the API using HTTP Basic Auth with their username and
password.

For more information about this demo application, see...
"""

import logging
import os

from pyramid.config import Configurator

logging.basicConfig(format='[%(asctime)s] [%(process)d] [%(levelname)s] %(name)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S %z',
                    level=logging.INFO)


def create_app():
    settings = settings_from_environ()
    config = Configurator(settings=settings)

    config.include('memex')

    config.include('.auth')
    config.include('.db')

    return config.make_wsgi_app()


def settings_from_environ():
    settings = {}
    if 'ELASTICSEARCH_HOST' in os.environ:
        settings['es.host'] = os.environ['ELASTICSEARCH_HOST']
    if 'ELASTICSEARCH_INDEX' in os.environ:
        settings['es.index'] = os.environ['ELASTICSEARCH_INDEX']
    if 'DATABASE_URL' in os.environ:
        settings['sqlalchemy.url'] = os.environ['DATABASE_URL']
    return settings
