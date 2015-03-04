# -*- coding: utf-8 -*-
import os

from clik import App
from elasticsearch import Elasticsearch
from pyramid import paster
import webassets.script

from h import __version__, reindexer


ENV_OVERRIDES = {
    'MODEL_CREATE_ALL': 'False',
    'MODEL_DROP_ALL': 'False',
    'SECRET_KEY': 'notsecret',
}
os.environ.update(ENV_OVERRIDES)

version = __version__
description = """\
The Hypothesis Project Annotation System
"""

command = App(
    'hypothesis',
    version=version,
    description=description,
)


@command(usage='config_uri')
def init_db(args, console):
    """Create database tables and elasticsearch indices."""

    if len(args) != 1:
        console.error('Requires a config file argument')
        return 2

    config_uri = args[0]

    # Force model creation using the MODEL_CREATE_ALL env var
    os.environ['MODEL_CREATE_ALL'] = 'True'

    # Start the application, triggering model creation
    paster.setup_logging(config_uri)
    paster.bootstrap(config_uri)


@command(usage='config_file')
def assets(args, console):
    """Build the static assets."""

    if len(args) != 1:
        console.error('Requires a config file argument')
        return 2

    config_uri = args[0]

    paster.setup_logging(config_uri)
    env = paster.bootstrap(config_uri)

    assets_env = env['request'].webassets_env
    webassets.script.main(['build'], assets_env)


@command()
def extension(args, console):
    console.error('This command has been removed. Please use the '
                  'hypothesis-buildext tool instead.')


@command(usage='config_file old_index new_index [alias]')
def reindex(args, console):
    """Reindex the annotations into a new Elasticsearch index"""
    if len(args) < 3:
        console.error('Please provide a config file and index names.')
        return 2

    config_uri = args[0]
    paster.setup_logging(config_uri)
    env = paster.bootstrap(config_uri)

    if 'es.host' in env['registry'].settings:
        host = env['registry'].settings['es.host']
        conn = Elasticsearch([host])
    else:
        conn = Elasticsearch()

    old_index = args[1]
    new_index = args[2]
    try:
        alias = args[3]
    except IndexError:
        alias = None

    r = reindexer.Reindexer(conn, interactive=True)

    r.reindex(old_index, new_index)

    if alias:
        r.alias(new_index, alias)

main = command.main
