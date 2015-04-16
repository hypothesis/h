# -*- coding: utf-8 -*-
from pyramid_layout.layout import layout_config


@layout_config(template='h:templates/layouts/base.html')
class BaseLayout(object):
    app = None
    controller = None
    csp = None
    requirements = (('app', None),)

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.forms = {}

    def add_form(self, form):
        if form.formid in self.forms:
            raise ValueError('duplicate form id "%s"' % form.formid)
        self.forms[form.formid] = form

    def get_widget_requirements(self):
        requirements = []
        requirements.extend(self.requirements)
        for form in self.forms.values():
            requirements.extend(form.get_widget_requirements())
        return requirements

    def get_widget_resources(self):
        requirements = self.get_widget_requirements()
        return self.request.registry.resources(requirements)

    @property
    def xpath_polyfill_urls(self):
        return self.request.webassets_env['wgxpath'].urls()

    @property
    def url_polyfill_urls(self):
        return self.request.webassets_env['url'].urls()

    @property
    def app_inject_urls(self):
        return self.request.webassets_env['inject'].urls()

    @property
    def css_links(self):
        return self.get_widget_resources()['css']

    @property
    def js_links(self):
        return self.get_widget_resources()['js']


@layout_config(name='app', template='h:templates/layouts/base.html')
class AppLayout(BaseLayout):
    app = 'h'
    controller = 'AppController'
    requirements = (('app', None), ('account', None), ('topbar', None))


def includeme(config):
    config.include('pyramid_layout')
    config.scan(__name__)
