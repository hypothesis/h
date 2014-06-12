import json

from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config
from requests_oauthlib import OAuth2Session
from requests import Request

from h import events, views


@view_config(route_name='auth.wpd.login')
@view_config(route_name='auth.wpd.callback', renderer='h:templates/oauth.pt')
def login(request):
    registry = request.registry
    settings = registry.settings
    session = request.session

    key = settings['auth.wpd.client_id']
    secret = settings['auth.wpd.client_secret']
    code = request.params.get('code')
    state = session.get('oauth_state')
    scope = ['session']
    provider = OAuth2Session(key, scope=scope, state=state)

    authz_endpoint = request.route_url('auth.wpd.authorize')
    token_endpoint = request.route_url('auth.wpd.token')
    profile_endpoint = 'https://profile.accounts.webplatform.org/v1/session/read'

    if code is not None:
        try:
            assert request.params['state'] == session['oauth_state']
            req = Request('POST', token_endpoint,
                          data=json.dumps({
                              'client_id': key,
                              'client_secret': secret,
                              'code': code,
                          }))
            prepped = provider.prepare_request(req)
            provider.token = provider.send(prepped).json()
            provider._client.access_token = provider.token['access_token']
            result = provider.get(profile_endpoint)
            provider_login = result.json()['username']
            userid = 'acct:{}@notes.webplatform.org'.format(provider_login)
            event = events.LoginEvent(request, userid)
            registry.notify(event)
            result = views.model(request)
            request.layout_manager.layout.app = 'h'
            request.layout_manager.layout.controller = 'AppController'
            return dict(result=json.dumps(result))
        except:
            pass

    location, state = provider.authorization_url(authz_endpoint)
    location = location.replace('response_type=code&', '')
    session['oauth_state'] = state
    return HTTPFound(location=location)


@view_config(accept='application/json', name='app',
             request_param='__formid__', renderer='json')
def logout(request):
    event = events.LogoutEvent(request)
    request.registry.notify(event)
    return views.app(request)


def includeme(config):
    registry = config.registry
    settings = registry.settings

    default_authz = 'https://oauth.accounts.webplatform.org/v1/authorization'
    authz_endpoint = settings.get('auth.wpd.authorize', default_authz)
    config.add_route('auth.wpd.authorize', authz_endpoint)

    default_token = 'https://oauth.accounts.webplatform.org/v1/token'
    token_endpoint = settings.get('auth.wpd.token', default_token)
    config.add_route('auth.wpd.token', token_endpoint)

    config.add_route('auth.wpd.login', '/wpd/login')
    config.add_route('auth.wpd.callback', '/wpd/callback')
    config.scan(__name__)
