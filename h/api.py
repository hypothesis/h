from annotator import auth, authz, store, es
from annotator.annotation import Annotation

from flask import Flask, g

from pyramid.httpexceptions import HTTPBadRequest
from pyramid.view import view_config
from pyramid.wsgi import wsgiapp2

from h import messages, models


@view_config(context='h.resources.APIFactory', request_method='POST',
             name='access_token', permission='access_token', renderer='string')
def access_token(request):
    """OAuth2 access token provider"""
    for name in [
        'client_id',
        'client_secret',
        'code',
        'state'
    ]:
        if name not in request.params:
            msg = '%s "%s".' % (messages.MISSING_PARAMETER, name)
            raise HTTPBadRequest(msg)

    raise NotImplementedError('OAuth provider not implemented yet.')


def authorize(annotation, action, user=None):
    action_field = annotation.get('permissions', {}).get(action, [])

    if not action_field:
        return True
    else:
        return authz.authorize(annotation, action, user)


def includeme(config):
    """Include the annotator-store API backend.

    Example INI file:

        [app:h]
        api.key: 00000000-0000-0000-0000-000000000000

    """

    store.UPDATE_FILTER_FIELDS = ('updated', 'consumer')
    app = Flask('annotator')  # Create the annotator-store app
    app.register_blueprint(store.store)  # and register the store api.

    # Set up the models
    settings = config.get_settings()
    if 'es.host' in settings:
        app.config['ELASTICSEARCH_HOST'] = settings['es.host']
    if 'es.index' in settings:
        app.config['ELASTICSEARCH_INDEX'] = settings['es.index']
    es.init_app(app)
    with app.test_request_context():
        try:
            Annotation.create_all()
        except:
            Annotation.update_settings()
            Annotation.create_all()

    # Configure authentication and authorization
    app.config['AUTHZ_ON'] = True

    def before_request():
        g.auth = auth.Authenticator(models.Consumer.get_by_key)
        g.authorize = authorize

    app.before_request(before_request)

    # Configure the API view -- version 1 is just an annotator.store proxy
    config.add_view(wsgiapp2(app), context='h.resources.APIFactory', name='v1')
    config.add_view(wsgiapp2(app), context='h.resources.APIFactory',
                    name='current')

    # And pick up the token view
    config.scan(__name__)
