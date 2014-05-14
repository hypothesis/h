# -*- coding: utf-8 -*-
import json
from os import makedirs, mkdir, walk
from os.path import abspath, exists, join, normpath
from shutil import copyfile, rmtree
from urlparse import urljoin, urlparse, urlunparse, uses_netloc, uses_relative

from chameleon.zpt.template import PageTextTemplateFile
from clik import App
import elasticsearch
from gunicorn import config, util
from gunicorn.app.pasterapp import load_pasteapp, paste_config
from gunicorn.app.wsgiapp import WSGIApplication
from pyramid.config import Configurator
from pyramid.events import BeforeRender, ContextFound
from pyramid.paster import get_appsettings
from pyramid.path import AssetResolver
from pyramid.request import Request
from pyramid.scripts import pserve
from pyramid.scripting import prepare
from pyramid.settings import asbool
from pyramid.view import render_view
from pyramid_basemodel import bind_engine
import requests
from sqlalchemy import engine_from_config
import urlparse

from h import __version__, api


class Application(WSGIApplication):

    """A Gunicorn Paster Application

    Extends the base :class:`gunicorn.app.wsgiapp.WSGIApplication` class to
    skip processing of command line arguments and directly load a configuration
    from a configuration file.

    TODO: remove in favor of gunicorn.app.base.BaseApplication customization
    when Gunicorn R19 is released.
    """

    def __init__(self, filename, settings=None):
        self.relpath = util.getcwd()
        self.cfgpath = abspath(normpath(join(self.relpath, filename)))
        self.cfgurl = 'config:' + self.cfgpath
        self.settings = settings
        super(Application, self).__init__()

    def load_config(self):
        self.cfg = config.Config()
        self.cfg.set('paste', self.cfgurl)
        self.cfg.set('logconfig', self.cfgpath)

        cfg = paste_config(self.cfg, self.cfgurl, self.relpath, self.settings)

        for k, v in cfg.items():
            self.cfg.set(k.lower(), v)

        default_config = config.get_default_config_file()
        if default_config is not None:
            self.load_config_from_file(default_config)

    def load_pasteapp(self):
        self.chdir()
        return load_pasteapp(self.cfgurl, self.relpath, self.settings)


def get_config(args):
    if len(args) == 0:
        args.append('development.ini')
        args.append('--reload')

    settings = get_appsettings(args[0])
    settings['basemodel.should_create_all'] = False
    settings['basemodel.should_drop_all'] = False

    return dict(settings=settings)

version = __version__
description = """\
The Hypothes.is Project Annotation System
"""

command = App(
    'hypothesis',
    version=version,
    description=description,
    opts=pserve.PServeCommand.parser.option_list[1:],
    args_callback=get_config,
)

# Teach urlparse about extension schemes
uses_netloc.append('chrome-extension')
uses_relative.append('chrome-extension')

# Fetch an asset spec resolver
resolve = AssetResolver().resolve


def add_base_url(event):
    request = event['request']

    assets_env = request.webassets_env
    view_name = getattr(request, 'view_name', None)

    if view_name == 'embed.js' and not assets_env.debug:
        base_url = join(request.webassets_env.url, 'app.html')
    else:
        base_url = request.resource_url(request.context, 'app')

    event['base_url'] = base_url


def app(context, request):
    assets_dir = request.webassets_env.directory
    app_file = join(assets_dir, 'app.html')
    request.accept = 'text/html'
    with open(app_file, 'w') as f:
        f.write(render_view(context, request, name='app'))


def embed(context, request):
    assets_dir = request.webassets_env.directory
    embed_file = join(assets_dir, 'js/embed.js')

    setattr(request, 'view_name', 'embed.js')
    with open(embed_file, 'w') as f:
        f.write(render_view(context, request, name='embed.js'))
    delattr(request, 'view_name')


def manifest(context, request):
    # Chrome is strict about the format of the version string
    ext_version = '.'.join(version.replace('-', '.').split('.')[:4])
    assets_url = request.webassets_env.url
    manifest_file = resolve('h:browser/chrome/manifest.json').abspath()
    manifest_json_file = join('./build/chrome', 'manifest.json')
    manifest_renderer = PageTextTemplateFile(manifest_file)
    with open(manifest_json_file, 'w') as f:
        src = urljoin(request.resource_url(context), assets_url)
        f.write(manifest_renderer(src=src, version=ext_version))


def chrome(env):
    registry = env['registry']
    settings = registry.settings

    request = env['request']
    context = request.context

    registry.notify(ContextFound(request))  # pyramid_layout attrs
    request.layout_manager.layout.csp = ''

    manifest(context, request)
    embed(context, request)

    if asbool(settings.get('webassets.debug', False)) is False:
        app(context, request)


def merge(src, dst):
    for src_dir, _, files in walk(src):
        dst_dir = src_dir.replace(src, dst)
        if not exists(dst_dir):
            mkdir(dst_dir)
        for f in files:
            src_file = join(src_dir, f)
            dst_file = join(dst_dir, f)
            copyfile(src_file, dst_file)


@command(usage='CONFIG_FILE')
def init_db(settings):
    """Create the database models."""
    store = api.store.store_from_settings(settings)
    api.store.create_db(store)

    engine = engine_from_config(settings, 'sqlalchemy.')
    bind_engine(engine, should_create=True)

# Helper function to create an ES connection
def connect_es(host):
    parsed = urlparse.urlparse(host)

    connargs = {
      'host': parsed.hostname,
    }

    username = parsed.username
    password = parsed.password
    if username is not None or password is not None:
        connargs['http_auth'] = ((username or ''), (password or ''))

    if parsed.port is not None:
        connargs['port'] = parsed.port

    if parsed.path:
        connargs['url_prefix'] = parsed.path

    conn = elasticsearch.Elasticsearch(
        hosts=[connargs],
        connection_class=elasticsearch.Urllib3HttpConnection)

    return conn


@command(usage='annotation_id')
def fetch_from_prod(args, console, settings):
    """Import an annotation from the production db to the local db"""
    if len(args) == 1:
        console.error("You must supply an annotation ID!")
        return 2
    else:
        id = args[1]

        try:
          es_host = settings["es.host"]
          console.error("Checking with local ES database at " + es_host + " ...")
          conn = connect_es(es_host)
          r = conn.get(index="annotator", doc_type="annotation", id=id)
          console.error("The wanted annotation already exists locally!")
          return 2

        except elasticsearch.exceptions.NotFoundError:
          console.error("OK, the wanted annotation does not exist locally.")
        except err:
          console.error("Error: can't task to ES!");
          return 2

        console.error("Fetching annotation" + id)
        uri = "https://api.hypothes.is/annotations/" + id
        result = requests.get(uri)
        if result.status_code != 200:
            console.error(result.text)
            return 2

        annotation = result.json()

        console.error("Creating annotation locally...")

        r = conn.index(index="annotator",
                       doc_type="annotation",
                       id=id,
                       body=annotation,
                       refresh=True)

        console.error("Inserted annotation to local DB.")


@command(usage='config_file')
def assets(settings):
    """Build the static assets."""
    config = Configurator(settings=settings)
    config.include('h.assets')
    for bundle in config.get_webassets_env():
        bundle.urls()


@command(usage='config_file base_url [static_url]')
def extension(args, console, settings):
    """Build the browser extensions.

    The first argument is the base URL of an h installation:

      http://localhost:5000

    An optional second argument can be used to specify the location for static
    assets.

    Examples:

      http://static.example.com/
      chrome-extension://extensionid/public
    """
    if len(args) == 1:
        console.error('You must supply a url to the hosted backend.')
        return 2
    elif len(args) == 2:
        assets_url = settings['webassets.base_url']
    else:
        settings['webassets.base_url'] = args[2]
        assets_url = args[2]

    base_url = args[1]

    # Fully-qualify the static asset url
    parts = urlparse(assets_url)
    if not parts.netloc:
        base = urlparse(base_url)
        parts = (base.scheme, base.netloc,
                 parts.path, parts.params,
                 parts.query, parts.fragment)
        assets_url = urlunparse(parts)

    # Set up the assets url and source path mapping
    settings['webassets.base_dir'] = abspath('./build/chrome/public')
    settings['webassets.base_url'] = assets_url
    settings['webassets.paths'] = json.dumps({
        resolve('h:').abspath(): assets_url
    })

    # Remove any existing build
    if exists('./build/chrome'):
        rmtree('./build/chrome')

    # Copy over all the assets
    assets(settings)
    makedirs('./build/chrome/public/lib/images')
    merge('./pdf.js/build/chromium', './build/chrome')
    merge('./h/browser/chrome', './build/chrome')
    merge('./h/images', './build/chrome/public/images')
    merge('./h/lib/images', './build/chrome/public/lib/images')

    config = Configurator(settings=settings)
    config.include('h')
    config.add_subscriber(add_base_url, BeforeRender)
    config.commit()

    # Build it
    request = Request.blank('/app', base_url=base_url)
    chrome(prepare(registry=config.registry, request=request))


@command(usage='[options] config_uri')
def serve(args):
    """Manage the server.

    With no arguments, starts the server in development mode using the
    configuration found in `deveopment.ini` and a hot code reloader enabled.

    Otherwise, acts as simple alias to the pserve command.
    """
    pserve.PServeCommand(['hypothesis'] + args).run()


main = command.main
