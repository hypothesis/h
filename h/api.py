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


def includeme(config):
    """Include the annotator-store API backend.

    Example INI file:

        [app:h]
        api.key: 00000000-0000-0000-0000-000000000000

    """

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

    # Configure authentication (ours) and authorization (store)
    authenticator = auth.Authenticator(models.Consumer.get_by_key)

    def before_request():
        g.auth = authenticator
        g.authorize = authz.authorize

    app.before_request(before_request)

    # Configure the API view -- version 1 is just an annotator.store proxy
    config.add_view(wsgiapp2(app), context='h.resources.APIFactory', name='v1')
    config.add_view(wsgiapp2(app), context='h.resources.APIFactory',
                    name='current')

    # And pick up the token view
    config.scan(__name__)
