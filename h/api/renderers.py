# -*- coding: utf-8 -*-
def events_renderer_factory(info):
    def _consume_events(value):
        for event in value:
            if event is None:
                yield ':'
            else:
                if 'data' in event:
                    yield 'data:{}\n'.format(event['data'])
                if 'event' in event:
                    yield 'event:{}\n'.format(event['event'])
                if 'id' in event:
                    yield 'id:{}\n'.format(event['id'])
            yield '\n'

    def _render(value, system):
        request = system.get('request')
        if request is not None:
            response = request.response
            ct = response.content_type
            if ct == response.default_content_type:
                response.content_type = 'text/event-stream'

        response.app_iter = _consume_events(value)
        return None

    return _render
