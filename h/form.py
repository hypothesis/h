# -*- coding: utf-8 -*-
"""
Configure deform to use custom templates.

Sets up the form handling and rendering library, deform, to use our own custom
form templates in preference to the defaults. Uses `deform_jinja2` to provide
the fallback templates in Jinja2 format, which we can then extend and modify as
necessary.
"""
import deform
import jinja2
import pyramid_jinja2
from pyramid.path import AssetResolver


SEARCH_PATHS = (
    'h:templates/deform/',
    'deform_jinja2:bootstrap_templates/',
)


class Jinja2Renderer(object):
    """
    An alternate Deform renderer that uses Jinja2 to render templates.

    We supply our own Jinja2 renderer because deform_jinja2's one doesn't
    support autoescaping.
    """

    def __init__(self, base_env):
        """
        Return a new callable Jinja2Renderer object.

        :param base_env: the initial Jinja2 environment that this renderer's
            Jinja2 environment will be created as an overlay of
        :type base_env: :py:class:`jinja2.Environment`
        """
        self._base_env = base_env
        self._env = None

    def _get_env(self):
        """
        Return this renderer's Jinja2 environment.

        Initialize the environment if it hasn't been initialized already.
        """
        if not self._env:
            resolver = AssetResolver()
            searchpath = [resolver.resolve(path).abspath()
                          for path in SEARCH_PATHS]
            loader = pyramid_jinja2.SmartAssetSpecLoader(searchpath)
            self._env = self._base_env.overlay(autoescape=True, loader=loader)
        return self._env

    def __call__(self, template_name, **kwargs):
        """Return the given template rendered with the given keyword args."""
        if not template_name.endswith('.jinja2'):
            template_name += '.jinja2'

        template = self._get_env().get_template(template_name)

        return jinja2.Markup(template.render(**kwargs))


def initialize_deform_renderer(config):
    deform.Form.set_default_renderer(
        Jinja2Renderer(config.get_jinja2_environment()))


def includeme(config):
    config.action(None, initialize_deform_renderer, args=[config])
