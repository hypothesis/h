from deform import Field
from pyramid_layout.layout import layout_config


@layout_config(template='h:templates/base.pt')
class BaseLayout(object):
    requirements = ()

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
        return Field.default_resource_registry(requirements)

    @property
    def css_links(self):
        return self.get_widget_resources()['css']

    @property
    def js_links(self):
        return self.get_widget_resources()['js']


@layout_config(context='h.resources.AppFactory',
               template='h:templates/base.pt')
class AppLayout(BaseLayout):
    requirements = (('app', None),)


@layout_config(context='h.resources.RootFactory',
               template='h:templates/base.pt')
class SiteLayout(BaseLayout):
    requirements = (('site', None),)


def includeme(config):
    config.include('pyramid_layout')
    config.scan(__name__)
