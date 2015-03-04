"""
:mod:`h.buildext` is a utility to build the Hypothesis browser extensions. It
is exposed as the command-line utility hypothesis-buildext.
"""
import argparse
import errno
import logging
import os
import os.path
import shutil
import sys
import textwrap
import urlparse

from jinja2 import Template
from pyramid import paster
from pyramid.events import ContextFound
from pyramid.path import AssetResolver
from pyramid.request import Request
from pyramid.view import render_view

import h

log = logging.getLogger('h.buildext')

# Teach urlparse about extension schemes
urlparse.uses_netloc.append('chrome-extension')
urlparse.uses_relative.append('chrome-extension')
urlparse.uses_netloc.append('resource')
urlparse.uses_relative.append('resource')

# Fetch an asset spec resolver
resolve = AssetResolver().resolve


def build_extension_common(env, src, dest, bundle_assets=False):
    """
    Copy the contents of src to dest, including some generic extension helpers
    scripts and, if necessary, a full complement of bundled static assets.
    """
    request = env['request']

    request.registry.notify(ContextFound(request))  # pyramid_layout attrs
    request.layout_manager.layout.csp = ''

    content_dir = request.webassets_env.directory

    # Make sure we use the bundled app.html if we're bundling assets
    if bundle_assets:
        request.registry.settings['h.use_bundled_app_html'] = True

    # Remove any existing build
    if os.path.exists(dest):
        shutil.rmtree(dest)

    # Copy the extension code
    os.makedirs(dest)
    copytree(src, dest)

    # Create the new build directory
    try:
        os.makedirs(content_dir)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

    # Change to the output directory
    old_dir = os.getcwd()
    os.chdir(dest)

    # Copy over the config and destroy scripts
    shutil.copyfile('../../h/static/extension/destroy.js',
                    content_dir + '/destroy.js')
    shutil.copyfile('../../h/static/extension/config.js',
                    content_dir + '/config.js')

    # Build the app html and copy assets if they are being bundled
    if bundle_assets:
        copytree('../../h/static/images', content_dir + '/images')

        # Copy over the vendor assets since they won't be processed otherwise
        if request.webassets_env.debug:
            os.makedirs(content_dir + '/scripts/vendor')
            copytree('../../h/static/scripts/vendor',
                     content_dir + '/scripts/vendor')

        with open(content_dir + '/app.html', 'w') as fp:
            data = render_view(request.context, request, 'app.html')
            fp.write(data)

    with open(content_dir + '/embed.js', 'w') as fp:
        data = render_view(request.context, request, 'embed.js')
        fp.write(data)

    # Reset the CWD
    os.chdir(old_dir)


def copytree(src, dst):
    """
    Copy a tree from src to dst, without complaining if dst already contains
    some directories in src like :func:`shutil.copytree`.

    Behaves identically to ``cp src/* dst/``.
    """
    if not os.path.exists(dst):
        os.mkdir(dst)
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            copytree(s, d)
        else:
            shutil.copyfile(s, d)


def chrome_manifest(request):
    # Chrome is strict about the format of the version string
    ext_version = '.'.join(h.__version__.replace('-', '.').split('.')[:4])
    manifest_file = open('h/browser/chrome/manifest.json')
    manifest_tpl = Template(manifest_file.read())
    src = request.resource_url(request.context)
    # We need to use only the host and port for the CSP script-src when
    # developing. If we provide a path such as /assets the CSP check fails.
    # See:
    #
    #   https://developer.chrome.com/extensions/contentSecurityPolicy#relaxing-remote-script
    if urlparse.urlparse(src).hostname not in ('localhost', '127.0.0.1'):
        src = urlparse.urljoin(src, request.webassets_env.url)
    return manifest_tpl.render(src=src, version=ext_version)


def firefox_manifest(request):
    ext_version = h.__version__.split('-')[0]
    manifest_file = open('h/browser/firefox/package.json')
    manifest_tpl = Template(manifest_file.read())
    return manifest_tpl.render(version=ext_version)


def get_env(config_uri, base_url):
    """
    Return a preconfigured paste environment object. Sets up the WSGI
    application and ensures that webassets knows to load files from
    ``h:static`` regardless of the ``webassets.base_dir`` setting.
    """
    request = Request.blank('', base_url=base_url)
    env = paster.bootstrap(config_uri, request)
    request.root = env['root']

    # Ensure that the webassets URL is absolute
    request.webassets_env.url = urlparse.urljoin(base_url,
                                                 request.webassets_env.url)

    # Disable webassets caching and manifest generation
    request.webassets_env.cache = False
    request.webassets_env.manifest = False

    # By default, webassets will use its base_dir setting as its search path.
    # When building extensions, we change base_dir so as to build assets
    # directly into the extension directories. As a result, we have to add
    # back the correct search path.
    request.webassets_env.append_path(resolve('h:static').abspath(),
                                      request.webassets_env.url)

    return env


def build_chrome(args):
    """
    Build the Chrome extension. You can supply the base URL of an h
    installation with which this extension will communicate, such as
    "http://localhost:5000" (the default) when developing locally or
    "https://hypothes.is" to talk to the production Hypothesis application.

    By default, the extension will load static assets (JavaScript/CSS/etc.)
    from the application you specify. This can be useful when developing, but
    when building a production extension for deployment to the Chrome Store you
    will need to specify an assets URL that links to the built assets within
    the Chrome Extension, such as:

        chrome-extension://<extensionid>/public
    """
    paster.setup_logging(args.config_uri)

    os.environ['WEBASSETS_BASE_DIR'] = os.path.abspath('./build/chrome/public')
    if args.assets is not None:
        os.environ['WEBASSETS_BASE_URL'] = args.assets

    env = get_env(args.config_uri, args.base)

    # Only bundle assets if we need to.
    assets_url = env['request'].webassets_env.url
    bundle_assets = assets_url.startswith('chrome-extension://')

    build_extension_common(env,
                           src='h/browser/chrome',
                           dest='build/chrome',
                           bundle_assets=bundle_assets)

    os.remove('build/chrome/karma.config.js')
    shutil.rmtree('build/chrome/test/')

    with open('build/chrome/manifest.json', 'w') as fp:
        data = chrome_manifest(env['request'])
        fp.write(data)


def build_firefox(args):
    """
    Build the Firefox extension. You must supply the base URL of an h
    installation with which this extension will communicate, such as
    "http://localhost:5000" (the default) when developing locally or
    "https://hypothes.is" to talk to the production Hypothesis application.

    By default, the extension will load static assets (JavaScript/CSS/etc.)
    from the application you specify. This can be useful when developing, but
    when building a production extension (such as for deployment to Mozilla
    Add-ons) you will need to specify an assets URL that links to the built
    assets within the extension, such as:

        resource://<extensionkey>/hypothesis/data
    """
    paster.setup_logging(args.config_uri)

    os.environ['WEBASSETS_BASE_DIR'] = os.path.abspath('./build/firefox/data')
    if args.assets is not None:
        os.environ['WEBASSETS_BASE_URL'] = args.assets

    env = get_env(args.config_uri, args.base)

    # Only bundle assets if we need to.
    assets_url = env['request'].webassets_env.url
    bundle_assets = assets_url.startswith('resource://')

    build_extension_common(env,
                           src='h/browser/firefox',
                           dest='build/firefox',
                           bundle_assets=bundle_assets)

    with open('build/firefox/package.json', 'w') as fp:
        data = firefox_manifest(env['request'])
        fp.write(data)


parser = argparse.ArgumentParser('hypothesis-buildext')
parser.add_argument('config_uri',
                    help='paster configuration URI')

subparsers = parser.add_subparsers(title='browser', dest='browser')
subparsers.required = True

parser_chrome = subparsers.add_parser(
    'chrome',
    help="build the Google Chrome extension",
    description=textwrap.dedent(build_chrome.__doc__),
    formatter_class=argparse.RawDescriptionHelpFormatter)
parser_chrome.add_argument('--base',
                           help='Base URL',
                           default='http://localhost:5000',
                           metavar='URL')
parser_chrome.add_argument('--assets',
                           help='A path (relative to base) or URL from which '
                                'to load the static assets',
                           default=None,
                           metavar='PATH/URL')

parser_firefox = subparsers.add_parser(
    'firefox',
    help="build the Mozilla Firefox extension",
    description=textwrap.dedent(build_firefox.__doc__),
    formatter_class=argparse.RawDescriptionHelpFormatter)
parser_firefox.add_argument('--base',
                            help='Base URL',
                            default='http://localhost:5000',
                            metavar='URL')
parser_firefox.add_argument('--assets',
                            help='A path (relative to base) or URL from which '
                                 'to load the static assets',
                            default=None,
                            metavar='PATH/URL')


BROWSERS = {
    'chrome': build_chrome,
    'firefox': build_firefox,
}


def main():
    args = parser.parse_args()
    BROWSERS[args.browser](args)


if __name__ == '__main__':
    main()
