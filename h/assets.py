# -*- coding: utf-8 -*-
import os

import json
from pyramid.settings import asbool, aslist
from pyramid.static import static_view

from h._compat import configparser


class _CachedFile(object):

    """
    Parses content from a file and caches the result.

    _CachedFile reads a file at a given path and parses the content using a
    provided loader.
    """

    def __init__(self, path, loader, auto_reload=False):
        """
        :param path: The path to the file to load.
        :param loader: A callable that will be passed the file object and
                       should return the parsed content.
        :param auto_reload: If True, the parsed content is discarded if the
                            mtime of the file changes.
        """
        self.path = path
        self.loader = loader
        self._mtime = None
        self._cached = None
        self._auto_reload = auto_reload

    def load(self):
        """
        Return the current content of the file parsed with the loader.

        The file is loaded using the provided loader when this is called the
        first time or if auto-reload is enabled and the file changed since the
        last call to ``load()``.
        """
        if self._mtime and not self._auto_reload:
            return self._cached

        current_mtime = os.path.getmtime(self.path)
        if not self._mtime or self._mtime < current_mtime:
            self._cached = self.loader(open(self.path))
            self._mtime = current_mtime
        return self._cached


class Environment(object):

    """
    Environment for generating URLs for Hypothesis' static assets.

    Static assets are grouped into named bundles, defined in an ini-format
    config file. The relative URL that should be used when serving a file from
    a bundle is defined in a JSON manifest file, which is generated by the
    static asset build pipeline.

    Environment reads the set of bundles from the config file
    and the mapping between the file path and the output URL
    from a JSON manifest file and provides the ability to retrieve the final
    URLs for a bundle via the urls() method.
    """

    def __init__(self, assets_base_url, bundle_config_path, manifest_path,
                 auto_reload=False):
        """
        Construct an Environment from the given configuration files.

        :param assets_base_url: The URL at which assets will be served,
                                excluding the trailing slash.
        :param bundle_config_path: Asset bundles config file.
        :param manifest_path: JSON file mapping file paths in the bundle config
                              file to cache-busted URLs.
        :param auto_reload: If True the config and manifest files are
                            automatically reloaded if they change.
        """
        self.assets_base_url = assets_base_url
        self.manifest = _CachedFile(manifest_path, json.load,
                                    auto_reload=auto_reload)
        self.bundles = _CachedFile(bundle_config_path, _load_bundles,
                                   auto_reload=auto_reload)

    def files(self, bundle):
        """Return the file paths for all files in a bundle."""
        bundles = self.bundles.load()
        return bundles[bundle]

    def urls(self, bundle):
        """
        Return asset URLs for all files in a bundle.

        Returns the URLs at which all files in a bundle are served,
        read from the asset manifest.
        """
        bundles = self.bundles.load()

        return [self.url(path) for path in bundles[bundle]]

    def url(self, path):
        """
        Return the cache-busted URL for an asset with a given path.
        """
        manifest = self.manifest.load()
        return '{}/{}'.format(self.assets_base_url, manifest[path])


def _add_cors_header(wrapped):
    def wrapper(context, request):
        # Add a CORS header to the response because static assets from
        # the sidebar are loaded into pages served by a different origin:
        # The domain hosting the page into which the sidebar has been injected
        # or embedded.
        #
        # Some browsers enforce cross-origin restrictions on certain types of
        # resources, eg. Firefox enforces same-domain policy for @font-face
        # unless a CORS header is provided.
        response = wrapped(context, request)
        response.headers.extend({
            'Access-Control-Allow-Origin': '*'
        })
        return response

    return wrapper


def _load_bundles(fp):
    """Read an asset bundle config from a file object."""
    parser = configparser.ConfigParser()
    parser.readfp(fp)
    return {k: aslist(v) for k, v in parser.items('bundles')}


# Site assets
assets_view = static_view('h:../build',
                          cache_max_age=None,
                          use_subpath=True)
assets_view = _add_cors_header(assets_view)


# Client assets
assets_client_view = static_view('h:../node_modules/hypothesis/build',
                                 cache_max_age=None,
                                 use_subpath=True)
assets_client_view = _add_cors_header(assets_client_view)


def includeme(config):
    auto_reload = asbool(config.registry.settings.get('h.reload_assets', False))

    config.add_view(route_name='assets', view=assets_view)
    config.add_view(route_name='assets_client', view=assets_client_view)

    assets_env = Environment('/assets',
                             'h/assets.ini',
                             'build/manifest.json',
                             auto_reload=auto_reload)
    assets_client_env = Environment('/assets/client',
                                    'h/assets_client.ini',
                                    'node_modules/hypothesis/build/manifest.json',
                                    auto_reload=auto_reload)

    # We store the environment objects on the registry so that the Jinja2
    # integration can be configured in app.py
    config.registry['assets_env'] = assets_env
    config.registry['assets_client_env'] = assets_client_env
