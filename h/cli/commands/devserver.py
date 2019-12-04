# -*- coding: utf-8 -*-

import os
import sys

import click


@click.command()
@click.option(
    "--https",
    envvar="USE_HTTPS",
    default=False,
    is_flag=True,
    help="Serve HTTPS rather than plain HTTP.",
)
@click.option(
    "--web/--no-web",
    default=True,
    help="Whether or not to run the Pyramid app process (default: --web).",
)
@click.option(
    "--ws/--no-ws",
    default=True,
    help="Whether or not to run the WebSocket process (default: --ws).",
)
@click.option(
    "--worker/--no-worker",
    default=True,
    help="Whether or not to run the Celery worker process (default: --worker).",
)
@click.option(
    "--assets/--no-assets",
    default=True,
    help="Whether or not to run the gulp watch process (default: --assets).",
)
@click.option(
    "--beat/--no-beat",
    default=True,
    help="Whether or not to run the celery beat process (default: --beat).",
)
def devserver(https, web, ws, worker, assets, beat):
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
        raise click.ClickException(
            "cannot import honcho: did you run `pip install -r requirements-dev.in` yet?"
        )

    os.environ["PYTHONUNBUFFERED"] = "true"
    if https:
        # These variable are read by our custom code in 'gunicorn.conf.py'
        os.environ["H_GUNICORN_CERTFILE"] = ".tlscert.pem"
        os.environ["H_GUNICORN_KEYFILE"] = ".tlskey.pem"

        # These variables are read in 'h/config.py'
        os.environ["APP_URL"] = "https://localhost:5000"
        os.environ["WEBSOCKET_URL"] = "wss://localhost:5001/ws"
    else:
        # These variables are read in 'h/config.py'
        os.environ["APP_URL"] = "http://localhost:5000"
        os.environ["WEBSOCKET_URL"] = "ws://localhost:5001/ws"

    m = Manager()
    if web:
        m.add_process(
            "web", "newrelic-admin run-program pserve --reload conf/development-app.ini"
        )

    if ws:
        m.add_process(
            "ws",
            "newrelic-admin run-program pserve --reload conf/development-websocket.ini",
        )

    if worker:
        m.add_process("worker", "hypothesis --dev celery worker -l INFO")

    if beat:
        m.add_process("beat", "hypothesis --dev celery beat")

    if assets:
        m.add_process("assets", "node_modules/.bin/gulp watch")

    m.loop()

    sys.exit(m.returncode)
