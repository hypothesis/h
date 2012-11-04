from annotator import auth, authz, store, es
from annotator.annotation import Annotation

from flask import Flask, g

from pyramid.httpexceptions import HTTPBadRequest, HTTPForbidden
from pyramid.view import view_config
from pyramid.wsgi import wsgiapp2

from h import messages, models


def personas(request):
    result = []
    if request.user:
        result.append({
            'username': request.user.username,
            'provider': request.host
        })
    return list(enumerate(result))


@view_config(context='h.resources.APIFactory', name='access_token',
             permission='access_token', renderer='string')
def token(request):
    """Get an API token for the logged in user."""

    if request.method == 'POST':  # OAuth2 access token endpoint
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

    else:  # Annotator token endpoint
        if not request.user:
            msg = messages.NOT_LOGGED_IN
            raise HTTPForbidden(msg)

        settings = request.registry.settings
        key = settings['api.key']
        consumer = models.Consumer.get_by_key(key)
        assert(consumer)

        user_id = 'acct:%s@%s' % (request.user.username, request.host)

        message = {
            'userId': user_id,
            'consumerKey': str(consumer.key),
            'ttl': consumer.ttl,
        }

        return auth.encode_token(message, consumer.secret)


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
