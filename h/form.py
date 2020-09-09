"""
Configure deform to use custom templates.

Sets up the form handling and rendering library, deform, to use our own custom
form templates in preference to the defaults.
"""
import deform
import jinja2
import pyramid_jinja2
from pyramid import httpexceptions
from pyramid.path import AssetResolver

from h import i18n

ENVIRONMENT_KEY = "h.form.jinja2_environment"

SEARCH_PATHS = ["h:templates/deform/"]


_ = i18n.TranslationString


class Jinja2Renderer:
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
        if not template_name.endswith(".jinja2"):
            template_name += ".jinja2"

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
    renderer = Jinja2Renderer(env, {"feature": request.feature})
    kwargs.setdefault("renderer", renderer)

    return deform.Form(*args, **kwargs)


def configure_environment(config):  # pragma: no cover
    """Configure the form template environment and store it in the registry."""
    base = config.get_jinja2_environment()
    config.registry[ENVIRONMENT_KEY] = create_environment(base)


def handle_form_submission(request, form, on_success, on_failure):
    """
    Handle the submission of the given form in a standard way.

    :param request: the Pyramid request

    :param form: the form that was submitted
    :type form: deform.form.Form

    :param on_success:
        A callback function to be called if the form validates successfully.

        This function should carry out the action that the form submission
        requests (for example for a change password form, this function would
        change the user's password) and return the view callable result that
        should be returned if this is not an XHR request.

        If on_success() returns ``None`` then ``handle_form_submission()``
        will return ``HTTPFound(location=request.url)`` by default.
    :type on_success: callable

    :param on_failure:
        A callback function that will be called if form validation fails in
        order to get the view callable result that should be returned if this is
        not an XHR request.
    :type on_failure: callable

    """
    try:
        appstruct = form.validate(request.POST.items())
    except deform.ValidationFailure:
        result = on_failure()
        request.response.status_int = 400
    else:
        result = on_success(appstruct)

        if result is None:
            result = httpexceptions.HTTPFound(location=request.url)

        if not request.is_xhr:
            request.session.flash(_("Success. We've saved your changes."), "success")

    return to_xhr_response(request, result, form)


def to_xhr_response(request, non_xhr_result, form):
    """
    Return an XHR response for the given ``form``, or ``non_xhr_result``.

    If the given ``request`` is an XMLHttpRequest then return an XHR form
    submission response for the given form (contains only the ``<form>``
    element as an HTML snippet, not the entire HTML page).

    If ``request`` is not an XHR request then return ``non_xhr_result``, which
    should be the result that the view callable would normally return if this
    were not an XHR request.

    :param request: the Pyramid request

    :param non_xhr_result: the view callable result that should be returned if
        ``request`` is *not* an XHR request

    :param form: the form that was submitted
    :type form: deform.form.Form

    """
    if not request.is_xhr:
        return non_xhr_result

    request.override_renderer = "string"
    return form.render()


def includeme(config):  # pragma: no cover
    config.action(None, configure_environment, args=(config,))
    config.add_request_method(create_form)
