from jinja2 import nodes
from jinja2.ext import Extension


class IncludeRawExtension(Extension):
    ''' A Jinja extension for requiring raw files using a familiar syntax.
        this is particularly useful for including JS template files which
        use the same syntax.'''

    tags = set(['include_raw'])

    def __init__(self, environment):
        # This check (for use of super in old-style classes) is broken in
        # latest pylint but fixed on pylint tip:
        #
        #     https://bitbucket.org/logilab/pylint/issue/24
        #
        # FIXME: remove when pylint>1.3.1 is released.
        #
        # pylint: disable=super-on-old-class
        super(IncludeRawExtension, self).__init__(environment)
        # pylint: enable=super-on-old-class

    def parse(self, parser):
        lineno = parser.stream.next().lineno
        filename = parser.parse_expression()
        env = self.environment

        # For some reason the current loader has no knowledge of the template
        # paths requiring us to manually build the template path.
        template_path = '%s:%s/%s' % ('h', 'templates', filename.value)
        template, _, _ = env.loader.get_source(env, template_path)

        return nodes.Const(template).set_lineno(lineno)
