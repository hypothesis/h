imports = [
  'h.identity'
  'h.helpers'
  'h.session'
]

AUTH_SESSION_ACTIONS = [
  'login'
  'logout'
  'register'
  'forgot'
  'activate'
  'edit_profile'
  'disable_user'
]


configure = [
  '$httpProvider', 'identityProvider', 'sessionProvider'
  ($httpProvider,   identityProvider,   sessionProvider) ->
    # Use the Pyramid XSRF header name
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRF-Token'

    identityProvider.checkAuthentication = [
      '$q', 'session',
      ($q,   session) ->
        (authCheck = $q.defer()).promise.then do ->
          session.load().$promise.then (data) ->
            if data.userid then authCheck.resolve data.csrf
            else authCheck.reject 'no session'
          , -> authCheck.reject 'request failure'
    ]

    identityProvider.forgetAuthentication = [
      'flash', 'session',
      (flash,   session) ->
        session.logout({}).$promise.catch (err) ->
          flash 'error', 'Sign out failed!'
          throw err
    ]

    identityProvider.requestAuthentication = [
      '$q', '$rootScope',
      ($q,   $rootScope) ->
        (authCheck = $q.defer()).promise.finally do ->
          $rootScope.$on 'auth', (event, err, data) ->
            if err then authCheck.reject err
            else authCheck.resolve data.csrf
    ]

    sessionProvider.actions.load =
      method: 'GET'
      withCredentials: true

    for action in AUTH_SESSION_ACTIONS
      sessionProvider.actions[action] =
        method: 'POST'
        params:
          __formid__: action
        withCredentials: true
]


angular.module('h.auth', imports, configure)
