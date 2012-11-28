from pyramid.decorator import reify
from pyramid_layout.layout import layout_config


@layout_config(template='h:templates/base.pt')
class BaseLayout(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.forms = {}

    def add_form(self, form):
        if form.formid in self.forms:
            raise ValueError('duplicate form id "%s"' % form.formid)
        self.forms[form.formid] = form

    @reify
    def resources(self):
        result = {'js': [], 'css': []}
        for form in self.forms.values():
            resources = form.get_widget_resources()
            for thing in ('js', 'css'):
                for source in resources[thing]:
                    if not source in result[thing]:
                        result[thing].append(source)
        return result

    @property
    def css_links(self):
        return self.resources['css']

    @property
    def js_links(self):
        return self.resources['js']


def includeme(config):
    config.include('pyramid_layout')
    config.scan(__name__)
