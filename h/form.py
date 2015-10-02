# -*- coding: utf-8 -*-
"""
Configure deform to use custom templates.

Sets up the form handling and rendering library, deform, to use our own custom
form templates in preference to the defaults. Uses `deform_jinja2` to provide
the fallback templates in Jinja2 format, which we can then extend and modify as
necessary.
"""


SEARCH_PATHS = (
    'h:templates/deform/',
    'deform_jinja2:bootstrap_templates/',
)


def includeme(_):
    from deform import Form
    from deform_jinja2 import jinja2_renderer_factory
    from deform_jinja2.translator import PyramidTranslator

    renderer = jinja2_renderer_factory(search_paths=SEARCH_PATHS,
                                       translator=PyramidTranslator())

    Form.set_default_renderer(renderer)
