import jinja2
import mock

from h import form


class TestJinja2Renderer(object):

    def test_it_initializes_an_overlay_environment_once(self):
        """It should call overlay() just once even if called more than once."""
        base_env = mock.Mock()
        renderer = form.Jinja2Renderer(base_env)

        # Call the renderer multiple times to render multiple templates.
        renderer('template_1')
        renderer('template_2')
        renderer('template_3')

        assert base_env.overlay.call_count == 1

    def test_it_passes_kwargs_to_render(self):
        template = mock.Mock()
        env = mock.Mock()
        env.get_template.return_value = template
        base_env = mock.Mock()
        base_env.overlay.return_value = env
        renderer = form.Jinja2Renderer(base_env)

        renderer('textinput', foo='foo', bar='bar')

        template.render.assert_called_once_with(foo='foo', bar='bar')

    def test_it_returns_the_rendered_template(self):
        renderer = form.Jinja2Renderer(jinja2.Environment())

        html = renderer('textinput', cstruct='', field=mock.Mock())

        assert html.startswith('<input')

    def test_it_returns_a_Markup_object(self):
        """It should return a Markup so the HTML will not get escaped later."""
        renderer = form.Jinja2Renderer(jinja2.Environment())

        html = renderer('textinput', cstruct='', field=mock.Mock())

        assert isinstance(html, jinja2.Markup)

    def test_it_escapes_user_text(self):
        """It should escape user text even if the base jinja2 env doesn't."""
        base_env = jinja2.Environment()  # This base env doesn't have
                                         # autoescape enabled.
        renderer = form.Jinja2Renderer(base_env)

        html = renderer(
            'textinput',
            cstruct='I am hacking you"><script>foo</script>',
            field=mock.Mock())

        assert '<script>foo</script>' not in html
