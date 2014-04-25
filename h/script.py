# -*- coding: utf-8 -*-
import json

import clik
from pyramid.scripts import pserve

from h import __version__

version = __version__
description = """\
The Hypothes.is Project Annotation System
"""

command = clik.App(
    'hypothesis',
    version=version,
    description=description,
    opts=pserve.PServeCommand.parser.option_list[1:],
)


@command(usage='CONFIG_FILE')
def init_db(args):
    """Create the database models."""
    from h.api import store
    from pyramid import paster

    settings_dict = paster.get_appsettings(args[0])
    app = store.store_from_settings(settings_dict)
    store.create_db(app)


@command(usage='CONFIG_FILE')
def assets(args, console):
    """Build the static assets."""

    if len(args) == 0:
        console.error('You must supply a paste configuration file.')
        return 2

    from pyramid import paster
    from pyramid_webassets import IWebAssetsEnvironment

    def build(env):
        asset_env = env['registry'].queryUtility(IWebAssetsEnvironment)
        for bundle in asset_env:
            bundle.urls()

    build(paster.bootstrap(args[0]))


@command(usage='CONFIG_FILE APP_URL [STATIC_URL]')
def extension(args, console):
    """Build the browser extensions.

    The first argument is the base URL of an h application:

      http://localhost:5000/app

    An optional second argument can be used to specify the location for static
    assets.

    Examples:

      http://static.example.com/
      chrome-extension://extensionid/public
    """

    if len(args) == 0:
        console.error('You must supply a paste configuration file.')
        return 2

    if len(args) < 2:
        console.error('You must supply a url to the hosted backend.')
        return 2

    import codecs
    from os import makedirs, mkdir, walk
    from os.path import abspath, exists, join
    from shutil import copyfile, rmtree
    from urlparse import (
        urljoin, urlparse, urlunparse, uses_netloc, uses_relative,
    )

    from chameleon.zpt.template import PageTextTemplateFile
    from pyramid.paster import bootstrap
    from pyramid.path import AssetResolver
    from pyramid.renderers import get_renderer, render
    from pyramid.settings import asbool
    from pyramid_webassets import IWebAssetsEnvironment

    from h import layouts

    resolve = AssetResolver().resolve

    def merge(src, dst):
        for src_dir, _, files in walk(src):
            dst_dir = src_dir.replace(src, dst)
            if not exists(dst_dir):
                mkdir(dst_dir)
            for f in files:
                src_file = join(src_dir, f)
                dst_file = join(dst_dir, f)
                copyfile(src_file, dst_file)

    def make_relative(request, url):
        assets_url = request.webassets_env.url
        if url.startswith(assets_url):
            return url[len(assets_url):].strip('/')
        return url

    def app(env, base_url=None):
        asset_env = env['registry'].queryUtility(IWebAssetsEnvironment)
        request = env['request']
        context = request.context

        base_template = get_renderer('h:templates/base.pt').implementation()

        api_url = request.registry.settings.get('api.url', None)
        api_url = api_url or urljoin(request.host_url, '/api/')

        app_layout = layouts.SidebarLayout(context, request)
        app_layout.csp = ''

        app_page = render(
            'h:templates/app.pt',
            {
                'base_url': base_url,
                'layout': app_layout,
                'main_template': base_template,
                'service_url': api_url,
            },
            request=request,
        )

        app_html_file = join(asset_env.directory, 'app.html')
        with codecs.open(app_html_file, 'w', 'utf-8-sig') as f:
            f.write(app_page)

    def chrome(env):
        registry = env['registry']
        request = env['request']
        asset_env = registry.queryUtility(IWebAssetsEnvironment)
        settings = registry.settings
        develop = asbool(settings.get('webassets.debug', False))

        # Root the request at the app url
        app_url = urlparse(args[1])
        request.host = app_url.netloc
        request.scheme = app_url.scheme
        app_url = urlunparse(app_url)

        # Fully-qualify the static asset url
        asset_url = urlparse(asset_env.url)
        if not asset_url.netloc:
            asset_url = (
                request.scheme,
                request.host,
                asset_url.path,
                asset_url.params,
                asset_url.query,
                asset_url.fragment,
            )
        asset_url = urlunparse(asset_url)

        # Configure the load path and output url
        asset_env.append_path(resolve('h:').abspath(), asset_url)
        asset_env.url = asset_url

        def getUrl(url):
            if not develop:
                rel = make_relative(request, url)
                if rel != url:
                    return "chrome.extension.getURL('public/%s')" % rel
            return '"%s"' % url

        if develop:
            # Load the app from the development server.
            app_expr = json.dumps(app_url)
        else:
            # Load the app from the extension bundle.
            app_expr = "chrome.extension.getURL('public/app.html')"
            # Build the app html
            app(env, base_url=app_url)

        embed = render(
            'h:templates/embed.txt',
            {
                'app': app_expr,
                'options': json.dumps({
                    'Heatmap': {
                        "container": '.annotator-frame',
                    },
                    'Toolbar': {
                        'container': '.annotator-frame',
                    },
                }),
                'role': json.dumps('host'),
                'inject': '[%s]' % ', '.join([
                    getUrl(url)
                    for url in asset_env['inject'].urls()
                ]),
                'jquery': getUrl(asset_env['jquery'].urls()[0]),
                'raf': getUrl(asset_env['raf'].urls()[0]),
            },
            request=request,
        )

        embed_js_file = join(asset_env.directory, 'js/embed.js')
        with codecs.open(embed_js_file, 'w', 'utf-8-sig') as f:
            f.write(embed)

        # Chrome is strict about the format of the version string
        ext_version = '.'.join(version.replace('-', '.').split('.')[:4])

        manifest_file = resolve('h:browser/chrome/manifest.json').abspath()
        manifest_renderer = PageTextTemplateFile(manifest_file)
        manifest = manifest_renderer(src=asset_url, version=ext_version)

        manifest_json_file = join('./build/chrome', 'manifest.json')
        with codecs.open(manifest_json_file, 'w', 'utf-8-sig') as f:
            f.write(manifest)

        # Due to Content Security Policy, the web font script cannot be inline.
        webfont = resolve('h:templates/webfont.js').abspath()
        copyfile(webfont, join(asset_env.directory, 'webfont.js'))

    # Build the chrome extension
    if exists('./build/chrome'):
        rmtree('./build/chrome')

    makedirs('./build/chrome/public/lib/images')

    merge('./pdf.js/build/chromium', './build/chrome')
    merge('./h/browser/chrome', './build/chrome')
    merge('./h/images', './build/chrome/public/images')
    merge('./h/lib/images', './build/chrome/public/lib/images')

    settings = {'webassets.base_dir': abspath('./build/chrome/public')}

    # Override static asset route generation with the STATIC_URL argument
    if len(args) > 2:
        settings.update({
            'webassets.base_url': args[2],
        })

    # Make sure urlparse understands chrome-extension:// URLs
    uses_netloc.append('chrome-extension')
    uses_relative.append('chrome-extension')

    chrome(bootstrap(args[0], options=settings))


@command(usage='[options] config_uri')
def serve(argv):
    """Manage the server.

    With no arguments, starts the server in development mode using the
    configuration found in `deveopment.ini` and a hot code reloader enabled.

    Otherwise, acts as simple alias to the pserve command.
    """
    if len(argv) == 1:  # Default to dev mode
        pserve.ensure_port_cleanup([('0.0.0.0', 5000)])
        argv.append('development.ini')
        argv.append('--reload')

    pserve.PServeCommand(['hypothesis'] + argv[1:]).run()


main = command.main
