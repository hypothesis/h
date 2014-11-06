# -*- coding: utf-8 -*-
import json
from os import chdir, getcwd, makedirs, mkdir, walk
from os.path import abspath, exists, join
from shutil import copyfile, rmtree
from urlparse import urljoin, urlparse, urlunparse, uses_netloc, uses_relative

from clik import App
from jinja2 import Template
from pyramid.config import Configurator
from pyramid.events import BeforeRender, ContextFound
from pyramid.paster import get_appsettings
from pyramid.path import AssetResolver
from pyramid.request import Request
from pyramid.scripting import prepare
from pyramid.view import render_view
from pyramid_basemodel import bind_engine
from sqlalchemy import engine_from_config

from h import __version__, api


def get_config(args):
    settings = get_appsettings(args[0])
    settings['basemodel.should_create_all'] = False
    settings['basemodel.should_drop_all'] = False
    settings['pyramid.includes'] = []

    return dict(settings=settings)

version = __version__
description = """\
The Hypothes.is Project Annotation System
"""

command = App(
    'hypothesis',
    version=version,
    description=description,
    args_callback=get_config,
)

# Teach urlparse about extension schemes
uses_netloc.append('chrome-extension')
uses_relative.append('chrome-extension')
uses_netloc.append('resource')
uses_relative.append('resource')

# Fetch an asset spec resolver
resolve = AssetResolver().resolve


def add_base_url(event):
    request = event['request']

    assets_env = request.webassets_env
    view_name = getattr(request, 'view_name', None)

    if view_name == 'embed.js' and assets_env.url.startswith('chrome-extension'):
        base_url = join(request.webassets_env.url, '')
    else:
        base_url = request.resource_url(request.context, '')

    event['base_url'] = base_url


def app(app_path, context, request):
    with open(app_path, 'w') as f:
        f.write(render_view(context, request, name='app.html'))


def embed(embed_path, context, request):
    setattr(request, 'view_name', 'embed.js')
    with open(embed_path, 'w') as f:
        f.write(render_view(context, request, name='embed.js'))
    delattr(request, 'view_name')


def manifest(context, request):
    # Chrome is strict about the format of the version string
    ext_version = '.'.join(version.replace('-', '.').split('.')[:4])
    assets_url = request.webassets_env.url
    manifest_file = resolve('h:browser/chrome/manifest.json').stream()
    manifest_tpl = Template(manifest_file.read())
    with open('manifest.json', 'w') as f:
        src = urljoin(request.resource_url(context), assets_url)
        f.write(manifest_tpl.render(src=src, version=ext_version))


def chrome(env):
    registry = env['registry']
    request = env['request']
    request.root = env['root']
    context = request.context

    registry.notify(ContextFound(request))  # pyramid_layout attrs
    request.layout_manager.layout.csp = ''

    # Remove any existing build
    if exists('./build/chrome'):
        rmtree('./build/chrome')

    # Create the new build directory
    makedirs('./build/chrome/public')

    # Change to the output directory
    old_dir = getcwd()
    chdir('./build/chrome')

    # Copy the extension code
    merge('../../h/browser/chrome', './')

    # Copy over the bootstrap and destroy scripts
    copyfile('../../h/static/bootstrap.js', './public/bootstrap.js')
    copyfile('../../h/static/extension/destroy.js', './public/destroy.js')
    copyfile('../../h/static/extension/config.js', './public/config.js')

    # Build the app html and copy assets if they are being bundled
    if request.webassets_env.url.startswith('chrome-extension://'):
        makedirs('./public/styles/images')
        merge('../../h/static/styles/images', './public/styles/images')
        merge('../../h/static/images', './public/images')
        merge('../../h/static/fonts', './public/fonts')
        copyfile('../../h/static/styles/icomoon.css', './public/styles/icomoon.css')

        # Copy over the vendor assets since they won't be processed otherwise
        if request.webassets_env.debug:
            makedirs('./public/scripts/vendor')
            merge('../../h/static/scripts/vendor', './public/scripts/vendor')

        app('public/app.html', context, request)

    manifest(context, request)
    embed('public/embed.js', context, request)

    # Reset the directory
    chdir(old_dir)


def firefox(env):
    registry = env['registry']
    request = env['request']
    context = request.context

    registry.notify(ContextFound(request))  # pyramid_layout attrs
    request.layout_manager.layout.csp = ''

    # Remove any existing build
    if exists('./build/firefox'):
        rmtree('./build/firefox')

    # Create the new build directory
    makedirs('./build/firefox/data')

    # Change to the output directory
    old_dir = getcwd()
    chdir('./build/firefox')

    # Copy the extension code
    merge('../../h/browser/firefox', './')

    # Copy over the bootstrap and destroy scripts
    copyfile('../../h/static/bootstrap.js', './data/bootstrap.js')
    copyfile('../../h/static/destroy.js', './data/destroy.js')

    # Build the app html and copy assets if they are being bundled
    if request.webassets_env.url.startswith('resource://'):
        makedirs('./data/styles/images')
        merge('../../h/static/styles/images', './data/styles/images')
        merge('../../h/static/images', './data/images')
        merge('../../h/static/fonts', './data/fonts')
        copyfile('../../h/static/styles/icomoon.css', './data/styles/icomoon.css')

        # Copy over the vendor assets since they won't be processed otherwise
        if request.webassets_env.debug:
            makedirs('./data/scripts/vendor')
            merge('../../h/static/scripts/vendor', './data/scripts/vendor')

        app('data/app.html', context, request)

    embed('data/embed.js', context, request)

    # Reset the directory
    chdir(old_dir)


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
    api.store_from_settings(settings)
    api.create_db()

    engine = engine_from_config(settings, 'sqlalchemy.')
    bind_engine(engine, should_create=True)


@command(usage='config_file')
def assets(settings):
    """Build the static assets."""
    config = Configurator(settings=settings)
    config.include('h.assets')
    for bundle in config.get_webassets_env():
        bundle.urls()


@command(usage='config_file browser base_url [static_url]')
def extension(args, console, settings):
    """Build the browser extensions.

    The first argument is the target browser for which to build the extension.
    Choices are: chrome or firefox.

    The second argument is the base URL of an h installation:

      http://localhost:5000

    An optional third argument can be used to specify the location for static
    assets.

    Examples:

      http://static.example.com/
      chrome-extension://extensionid/public
    """
    if len(args) == 1:
        console.error('You must supply a browser name: `chrome` or `firefox`.')
        return 2
    elif len(args) == 2:
        console.error('You must supply a url to the hosted backend.')
        return 2
    elif len(args) == 3:
        assets_url = settings['webassets.base_url']
    else:
        settings['webassets.base_url'] = args[3]
        assets_url = args[3]

    browser = args[1]
    base_url = args[2]

    # Fully-qualify the static asset url
    parts = urlparse(assets_url)
    if not parts.netloc:
        base = urlparse(base_url)
        parts = (base.scheme, base.netloc,
                 parts.path, parts.params,
                 parts.query, parts.fragment)
        assets_url = urlunparse(parts)

    # Set up the assets url and source path mapping
    if browser == 'chrome':
        settings['webassets.base_dir'] = abspath('./build/chrome/public')
    elif browser == 'firefox':
        settings['webassets.base_dir'] = abspath('./build/firefox/data')
    else:
        console.error('You must supply a browser name: `chrome` or `firefox`.')
        return 2

    settings['webassets.base_url'] = assets_url
    settings['webassets.paths'] = json.dumps({
        resolve('h:static').abspath(): assets_url
    })

    # Turn off the webassets cache and manifest
    settings['webassets.cache'] = None
    settings['webassets.manifest'] = None

    config = Configurator(settings=settings)
    config.include('h')
    config.add_subscriber(add_base_url, BeforeRender)
    config.commit()

    # Build it
    request = Request.blank('/app', base_url=base_url)
    globals()[browser](prepare(registry=config.registry, request=request))

    # XXX: Change when webassets allows setting the cache option
    # As of 0.10 it's only possible to pass a sass config  with string values
    try:
        rmtree('./build/' + browser + '/public/.sass-cache')
    except OSError:
        pass  # newer Sass doesn't write this it seems


main = command.main
