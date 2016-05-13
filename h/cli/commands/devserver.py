# -*- coding: utf-8 -*-

import os
import sys

import click


@click.command()
@click.option('--https',
              envvar='USE_HTTPS',
              default=False,
              is_flag=True,
              help='Serve HTTPS rather than plain HTTP.')
def devserver(https):
    """
    Run a development server.

    This command will start a development instance of h, consisting of a web
    application, Celery worker, and websocket server. It will also start a
    process which will watch and build the frontend assets.

    By default, the webserver will be accessible at:

        http://localhost:5000

    You can also pass the `--https` flag, which will look for a TLS certificate
    and key in PEM format in the current directory, in files called:

        .tlscert.pem
        .tlskey.pem

    If you use this flag, the webserver will be accessible at:

        https://localhost:5000

    If you wish this to be the default behaviour, you can set the
    USE_HTTPS environment variable.
    """
    try:
        from honcho.manager import Manager
    except ImportError:
        raise click.ClickException('cannot import honcho: did you run `pip install -e .[dev]` yet?')

    os.environ['PYTHONUNBUFFERED'] = 'true'
    if https:
        gunicorn_args = '--certfile=.tlscert.pem --keyfile=.tlskey.pem'
        os.environ['APP_URL'] = 'https://localhost:5000'
        os.environ['H_WEBSOCKET_URL'] = 'wss://localhost:5001/ws'
        os.environ['ALLOWED_ORIGINS'] = 'https://localhost:5000'
    else:
        gunicorn_args = ''
        os.environ['APP_URL'] = 'http://localhost:5000'
        os.environ['H_WEBSOCKET_URL'] = 'ws://localhost:5001/ws'

    m = Manager()
    m.add_process('web', 'gunicorn --reload --paste conf/development-app.ini %s' % gunicorn_args)
    m.add_process('ws', 'gunicorn --reload --paste conf/development-websocket.ini %s' % gunicorn_args)
    m.add_process('worker', 'hypothesis --dev celery worker --autoreload')
    m.add_process('assets', 'gulp watch')
    m.loop()

    sys.exit(m.returncode)
