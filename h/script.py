# -*- coding: utf-8 -*-
import json
from os import makedirs, mkdir, walk
from os.path import abspath, exists, join
from shutil import copyfile, rmtree
from urlparse import urljoin, urlparse, urlunparse, uses_netloc, uses_relative

from chameleon.zpt.template import PageTextTemplateFile
from clik import App
from pyramid.config import Configurator
from pyramid.events import ContextFound
from pyramid.paster import get_appsettings
from pyramid.path import AssetResolver
from pyramid.request import Request
from pyramid.scripts import pserve
from pyramid.scripting import prepare
from pyramid.settings import asbool
from pyramid.view import render_view
from pyramid_basemodel import bind_engine
from sqlalchemy import engine_from_config

from h import __version__, api, create_app


def get_config(argv):
    if len(argv) == 1:
        argv.append('--reload')
        argv.append('development.ini')
        cf = argv[2]
    else:
        cf = argv[1]

    settings = get_appsettings(cf)
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


def app(context, request):
    assets_dir = request.webassets_env.directory
    app_file = join(assets_dir, 'app.html')
    with open(app_file, 'w') as f:
        f.write(render_view(context, request, name='app'))


def embed(context, request):
    assets_dir = request.webassets_env.directory
    embed_file = join(assets_dir, 'js/embed.js')
    with open(embed_file, 'w') as f:
        f.write(render_view(context, request, name='embed.js'))


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

    registry.notify(ContextFound(request))
    request.layout_manager.layout.csp = ''

    embed(context, request)
    manifest(context, request)

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
    settings['webassets.base_dir'] = abspath('./build/chrome/public')

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

    # Build it
    wsgi = create_app(settings)
    request = Request.blank('/app', base_url=base_url)
    chrome(prepare(registry=wsgi.registry, request=request))


@command(usage='[options] config_uri')
def serve(argv):
    """Manage the server.

    With no arguments, starts the server in development mode using the
    configuration found in `deveopment.ini` and a hot code reloader enabled.

    Otherwise, acts as simple alias to the pserve command.
    """
    pserve.PServeCommand(['hypothesis'] + argv[1:]).run()


main = command.main
