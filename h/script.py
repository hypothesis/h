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
)


@command(usage='CONFIG_FILE')
def assets(args, console):
    """Build the static assets."""

    if len(args) == 0:
        console.error('You must supply a paste configuration file.')
        return 2

    from h import bootstrap
    from pyramid_webassets import IWebAssetsEnvironment

    def build(env):
        asset_env = env['registry'].queryUtility(IWebAssetsEnvironment)
        for bundle in asset_env:
            bundle.urls()

    bootstrap(args[0], config_fn=build)

@command
def tag(args, console):
    """ Tag the release """
    import time
    import random
    import os

    # Get a timestamp
    timestamp = time.asctime()


    dirH = os.path.dirname(__file__)

    # Get a random name for the release
    nameFileName = os.path.join(dirH, "lib", "names.txt")
    names = []
    for line in open(nameFileName):
        names.append(line[:-1])
    random.seed()
    index = random.randint(0, len(names)-1)
    name = names[index]
    names = []

    # Build the tag
    tag = timestamp + " (" + name + ")"
    console.error("Tagging release as '" + tag + "'.")

    # Write the release tag files on clientside and serverside
    clientTagFileName = os.path.join(dirH, "js", "release_tag.coffee")
    with open (clientTagFileName, "w") as tagfile:
        tagfile.write("window.hypothesis_release='" + tag + "'\n")

#  TODO: solve server-side version info
#    serverTagFileName = os.path.join(dirH, "release_tag.py")
#    with open (serverTagFileName, "w") as tagfile:
#        tagfile.write("hypothesis_release='" + tag + "'\n")


@command(usage='CONFIG_FILE APP_URL [STATIC_URL]')
def extension(args, console):
    """Build the browser extensions.

    Accepts one (optional) argument which is the base URL of an h server."""

    if len(args) == 0:
        console.error('You must supply a paste configuration file.')
        return 2

    if len(args) < 2:
        console.error('You must supply a url to the hosted backend.')
        return 2

    from codecs import open
    from os import makedirs
    from os.path import abspath, exists, join
    from shutil import copyfile, copytree, rmtree
    from urlparse import (
        urljoin, urlparse, urlunparse, uses_netloc, uses_relative,
    )

    from chameleon.zpt.template import PageTextTemplateFile
    from pyramid.path import AssetResolver
    from pyramid.renderers import get_renderer, render
    from pyramid.settings import asbool
    from pyramid_webassets import IWebAssetsEnvironment

    from h import bootstrap, layouts

    resolve = AssetResolver().resolve

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
        api_url = api_url or urljoin(request.host_url, '/api')

        app_layout = layouts.SidebarLayout(context, request)
        app_page = render(
            'h:templates/app.pt',
            {
                'base_url': base_url,
                'layout': {
                    'css_links': app_layout.css_links,
                    'js_links': app_layout.js_links,
                    'csp': '',
                    'inline_webfont': False,
                },
                'main_template': base_template,
                'request': request,
                'service_url': api_url,
            }
        )

        app_html_file = join(asset_env.directory, 'app.html')
        with open(app_html_file, 'w', 'utf-8-sig') as f:
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
            app_expr = "'%s'"  % app_url
        else:
            # Load the app from the extension bundle.
            app_expr = "chrome.extension.getURL('public/app.html')"
            # Build the app html
            app(env, base_url=app_url)

        embed = render(
            'h:templates/embed.txt',
            {
                'app': app_expr,
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
        with open(embed_js_file, 'w', 'utf-8-sig') as f:
            f.write(embed)

        # Chrome is strict about the format of the version string
        ext_version = '.'.join(version.replace('-', '.').split('.')[:4])

        manifest_file = resolve('h:browser/chrome/manifest.json').abspath()
        manifest_renderer = PageTextTemplateFile(manifest_file)
        manifest = manifest_renderer(src=asset_url, version=ext_version)

        manifest_json_file = join('./build/chrome', 'manifest.json')
        with open(manifest_json_file, 'w', 'utf-8-sig') as f:
            f.write(manifest)

        # Due to Content Security Policy, the web font script cannot be inline.
        webfont = resolve('h:templates/webfont.js').abspath()
        copyfile(webfont, join(asset_env.directory, 'webfont.js'))

    # Make sure the common build dir exists
    if not exists('./build'): makedirs('./build')

    # Build the chrome extension
    if exists('./build/chrome'): rmtree('./build/chrome')
    copytree(resolve('h:browser/chrome').abspath(), './build/chrome')
    copytree(resolve('h:images').abspath(), './build/chrome/public/images')
    copytree(resolve('h:lib').abspath(), './build/chrome/public/lib')

    settings = {'webassets.base_dir': abspath('./build/chrome/public')}

    # Override static asset route generation with the STATIC_URL argument
    if len(args) > 2:
        settings.update({
            'webassets.base_url': args[2],
        })

    # Make sure urlparse understands chrome-extension:// URLs
    uses_netloc.append('chrome-extension')
    uses_relative.append('chrome-extension')

    bootstrap(args[0], options=settings, config_fn=chrome)


@command
def start(args):
    """Start the server.

    With no arguments, starts the server in development mode using the
    configuration found in `deveopment.ini` and a hot code reloader enabled.
    """
    if not len(args):  # Default to dev mode
        pserve.ensure_port_cleanup([('0.0.0.0', 5000)])
        args.append('development.ini')
        args.append('--reload')

    pserve.main(['hypothesis'] + args)


main = command.main
