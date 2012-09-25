from annotator import auth, authz, store, es
from annotator.annotation import Annotation

from flask import Flask, g

from pyramid.httpexceptions import HTTPBadRequest, HTTPForbidden
from pyramid.view import view_config
from pyramid.wsgi import wsgiapp2

from h import messages, models


def get_consumer(request):
    if not request.params:
        settings = request.registry.settings

        key = settings['api.key']
        secret = settings.get('api.secret')
        ttl = settings.get('api.ttl')

        consumer = models.Consumer.get_by_key(key)
        if consumer is None and secret:
            consumer = models.Consumer(key)
            consumer.secret = secret
            consumer.ttl = ttl
    else:
        consumer = None
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

    return consumer


def personas(request):
    if request.user:
        return list(enumerate([request.user.user_name]))
    return []


@view_config(context='h.resources.APIFactory', name='access_token',
             permission='access_token', renderer='string')
def token(request):
    """Get an API token for the logged in user."""

    if not request.user:
        msg = messages.NOT_LOGGED_IN
        raise HTTPForbidden(msg)

    consumer = request.consumer
    # TODO make this deal with oid+realms, oauth etc
    user_id = 'acct:%s@%s' % (request.user.user_name, request.host)

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

    # Configure a reified request property for easy access to the API consumer
    # represented by the application or the request. See
    # :class:`h.models.Consumer` for details about this object.
    config.set_request_property(get_consumer, 'consumer', reify=True)

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
