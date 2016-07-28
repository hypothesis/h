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


ENVIRONMENT_KEY = 'h.form.jinja2_environment'

SEARCH_PATHS = (
    'h:templates/deform/',
    'deform_jinja2:bootstrap_templates/',
)


class Jinja2Renderer(object):
    """An alternate Deform renderer that uses Jinja2 to render templates."""

    def __init__(self, env, system=None):
        """
        Return a new callable Jinja2Renderer object.

        :param env: the Jinja2 environment used by this renderer
        :type env: :py:class:`jinja2.Environment`

        :param system: a dictionary of system renderer globals
        :type system: dict
        """
        self._env = env
        self._system = system if system is not None else {}

    def __call__(self, template_name, **kwargs):
        """Render the named template with the passed keywords as context."""
        if not template_name.endswith('.jinja2'):
            template_name += '.jinja2'

        template = self._env.get_template(template_name)
        context = self._system.copy()
        context.update(kwargs)

        return jinja2.Markup(template.render(context))


def create_environment(base):
    """
    Create a Jinja2 environment for rendering forms.

    Creates an overlay environment based on the passed `base` environment that
    is suitable for rendering the Deform templates.
    """
    # Build a template loader based on SEARCH_PATHS
    resolver = AssetResolver()
    searchpath = [resolver.resolve(path).abspath() for path in SEARCH_PATHS]
    loader = pyramid_jinja2.SmartAssetSpecLoader(searchpath)

    # Make an overlay environment from the main Jinja2 environment. See:
    #
    #   http://jinja.pocoo.org/docs/dev/api/#jinja2.Environment.overlay
    return base.overlay(autoescape=True, loader=loader)


def create_form(request, *args, **kwargs):
    """
    Create a :py:class:`deform.Form` instance for this request.

    This request method creates a :py:class:`deform.Form` object which (by
    default) will use the renderer configured in the :py:mod:`h.form` module.
    """
    env = request.registry[ENVIRONMENT_KEY]
    renderer = Jinja2Renderer(env, {
        'feature': request.feature,
    })
    kwargs.setdefault('renderer', renderer)

    return deform.Form(*args, **kwargs)


def configure_environment(config):  # pragma: no cover
    """Configure the form template environment and store it in the registry."""
    base = config.get_jinja2_environment()
    config.registry[ENVIRONMENT_KEY] = create_environment(base)


def includeme(config):  # pragma: no cover
    config.action(None, configure_environment, args=(config,))
    config.add_request_method(create_form)
