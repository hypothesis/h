# -*- coding: utf-8 -*-

import mock
import pytest

from h import form


class TestJinja2Renderer(object):

    def test_call_fetches_correct_templates(self, jinja2_env):
        renderer = form.Jinja2Renderer(jinja2_env)

        renderer('foo')
        renderer('foo.jinja2')
        renderer('bar/baz')
        renderer('bar/baz.jinja2')

        assert jinja2_env.get_template.call_args_list == [
            mock.call('foo.jinja2'),
            mock.call('foo.jinja2'),
            mock.call('bar/baz.jinja2'),
            mock.call('bar/baz.jinja2'),
        ]

    def test_call_passes_kwargs_to_render(self, jinja2_env, jinja2_template):
        renderer = form.Jinja2Renderer(jinja2_env)

        renderer('textinput', foo='foo', bar='bar')

        jinja2_template.render.assert_called_once_with({'foo': 'foo',
                                                        'bar': 'bar'})

    def test_call_passes_system_context_to_render(self, jinja2_env, jinja2_template):
        renderer = form.Jinja2Renderer(jinja2_env, {'bar': 'default'})

        renderer('textinput')
        renderer('textinput', foo='foo')
        renderer('textinput', foo='foo', bar='bar')

        assert jinja2_template.render.call_args_list == [
            mock.call({'bar': 'default'}),
            mock.call({'foo': 'foo', 'bar': 'default'}),
            mock.call({'foo': 'foo', 'bar': 'bar'}),
        ]

    @pytest.fixture
    def jinja2_env(self, jinja2_template):
        environment = mock.Mock(spec_set=['get_template'])
        environment.get_template.return_value = jinja2_template
        return environment

    @pytest.fixture
    def jinja2_template(self):
        return mock.Mock(spec_set=['render'])


class TestCreateEnvironment(object):
    def test_overlays_base_with_correct_args(self):
        base = mock.Mock(spec_set=['overlay'])

        form.create_environment(base)

        base.overlay.assert_called_once_with(autoescape=True, loader=mock.ANY)

    def test_loader_has_correct_paths(self):
        base = mock.Mock(spec_set=['overlay'])

        form.create_environment(base)
        _, kwargs = base.overlay.call_args
        loader = kwargs['loader']

        assert 'templates/deform' in loader.searchpath[0]
        assert 'bootstrap_templates' in loader.searchpath[1]


class TestCreateForm(object):
    def test_returns_form_object(self, Form, pyramid_request):
        result = form.create_form(pyramid_request, mock.sentinel.schema)

        assert result == Form.return_value

    def test_passes_args_including_renderer_to_form_ctor(self,
                                                         Form,
                                                         matchers,
                                                         pyramid_request):
        form.create_form(pyramid_request, mock.sentinel.schema, foo='bar')

        Form.assert_called_once_with(mock.sentinel.schema,
                                     foo='bar',
                                     renderer=matchers.instance_of(form.Jinja2Renderer))

    def test_adds_feature_client_to_system_context(self,
                                                   Form,
                                                   patch,
                                                   pyramid_request):
        Jinja2Renderer = patch('h.form.Jinja2Renderer')

        form.create_form(pyramid_request, mock.sentinel.schema)

        Jinja2Renderer.assert_called_once_with(
            mock.sentinel.jinja2_env,
            {'feature': pyramid_request.feature},
        )

    @pytest.fixture
    def Form(self, patch):
        return patch('deform.Form')

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.registry[form.ENVIRONMENT_KEY] = mock.sentinel.jinja2_env
        return pyramid_request
