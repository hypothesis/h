import clik

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


@command(usage='CONFIG_FILE')
def extension(args, console):
    """Build the browser extensions."""

    if len(args) == 0:
        console.error('You must supply a paste configuration file.')
        return 2

    from codecs import open
    from os import makedirs
    from os.path import abspath, exists, join
    from shutil import copyfile, copytree, rmtree
    from urlparse import urljoin

    from chameleon.zpt.template import PageTextTemplateFile
    from pyramid.path import AssetResolver
    from pyramid.renderers import get_renderer, render
    from pyramid_webassets import IWebAssetsEnvironment

    from h import bootstrap, layouts

    resolve = AssetResolver().resolve

    def make_relative(env, url):
        host_url = env['request'].host_url
        if url.startswith(host_url):
            return url[len(host_url) + 1:].strip('/')
        return url

    def app(env):
        asset_env = env['registry'].queryUtility(IWebAssetsEnvironment)
        request = env['request']
        context = request.context

        base_template = get_renderer('h:templates/base.pt').implementation()
        app_layout = layouts.AppLayout(context, request)
        app_page = render(
            'h:templates/app.pt',
            {
                'layout': {
                    'css_links': [
                        make_relative(env, href)
                        for href in app_layout.css_links
                    ],
                    'js_links': [
                        make_relative(env, src)
                        for src in app_layout.js_links
                    ],
                    'csp': '',
                    'inline_webfont': False,
                },
                'main_template': base_template,
            }
        )

        app_html_file = join(asset_env.directory, 'app.html')
        with open(app_html_file, 'w', 'utf-8-sig') as f:
            f.write(app_page)

    def chrome(env):
        asset_env = env['registry'].queryUtility(IWebAssetsEnvironment)
        settings = env['registry'].settings
        develop = settings.get('extension.develop', False)

        def getUrl(url):
            if develop:
                return '"%s"' % url

            rel = make_relative(env, url)
            if rel != url:
                return "chrome.extension.getURL('%s')" % rel

            return url

        if develop:
            # Load the app from the development server.
            env['request'].host = 'localhost:5000'
            base = env['request'].host_url
            app_url = getUrl(urljoin(base, 'app'))
        else:
            # Load the app from the extension bundle.
            app(env)  # Build the app html
            app_url = "chrome.extension.getURL('app.html')"

        embed = render(
            'h:templates/embed.txt',
            {
                'app': app_url,
                'inject': '[%s]' % ', '.join([
                    getUrl(url)
                    for url in asset_env['inject'].urls()
                ]),
                'jquery': getUrl(asset_env['jquery'].urls()[0]),
                'raf': getUrl(asset_env['raf'].urls()[0]),
            },
            request=env['request'],
        )

        embed_js_file = join(asset_env.directory, 'js/embed.js')
        with open(embed_js_file, 'w', 'utf-8-sig') as f:
            f.write(embed)

        # Chrome is strict about the format of the version string
        ext_version = '.'.join(version.replace('-', '.').split('.')[:4])

        manifest_file = join(asset_env.directory, 'manifest.json')
        manifest_renderer = PageTextTemplateFile(manifest_file)
        manifest = manifest_renderer(version=ext_version)

        manifest_json_file = join(asset_env.directory, 'manifest.json')
        with open(manifest_json_file, 'w', 'utf-8-sig') as f:
            f.write(manifest)

        # Due to Content Security Policy, the web font script cannot be inline.
        webfont = resolve('h:templates/webfont.js').abspath()
        copyfile(webfont, './build/chrome/webfont.js')

    if not exists('./build'):
        makedirs('./build')

    rmtree('./build/chrome')
    copytree(resolve('h:browser/chrome').abspath(), './build/chrome')
    bootstrap(
        args[0],
        options={
            'webassets.base_dir': abspath('./build/chrome'),
        },
        config_fn=chrome,
    )


@command
def start(args):
    """Start the server.

    With no arguments, starts the server in development mode using the
    configuration found in `deveopment.ini` and a hot code reloader enabled.
    """
    if not len(args):  # Default to dev mode
        args.append('development.ini')
        args.append('--reload')
        args.append('--monitor-restart')

    from pyramid.scripts.pserve import ensure_port_cleanup, main

    ensure_port_cleanup([('0.0.0.0', 5000)])
    main(['hypothesis'] + args)


main = command.main
