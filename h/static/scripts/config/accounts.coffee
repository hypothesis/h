angular = require('angular')

SESSION_ACTIONS = [
  'login'
  'logout'
  'register'
  'forgot_password'
  'reset_password'
  'edit_profile'
  'disable_user'
]


module.exports = [
  '$httpProvider', '$provide', 'identityProvider', 'sessionProvider'
  ($httpProvider,   $provide,   identityProvider,   sessionProvider) ->
    # Pending authentication check
    authCheck = null

    # Use the Pyramid XSRF header name
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRF-Token'

    # Provide an XSRF token for the session provider
    $provide.constant('xsrf', token: null)

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
      '$q', 'flash', 'session',
      ($q,   flash,   session) ->
        session.logout({}).$promise
        .then ->
          authCheck = $q.defer()
          authCheck.reject 'no session'
          return null
        .catch (err) ->
          flash.error('Sign out failed!')
          throw err
    ]

    identityProvider.requestAuthentication = [
      '$q', '$rootScope',
      ($q,   $rootScope) ->
        authCheck.promise.catch ->
          (authRequest = $q.defer()).promise.finally do ->
            $rootScope.$on 'auth', (event, err, data) ->
              if err then authRequest.reject err
              else authRequest.resolve data.csrf
    ]

    sessionProvider.actions.load =
      method: 'GET'
      withCredentials: true

    sessionProvider.actions.profile =
      method: 'GET'
      params:
        __formid__: 'profile'
      withCredentials: true

    for action in SESSION_ACTIONS
      sessionProvider.actions[action] =
        method: 'POST'
        params:
          __formid__: action
        withCredentials: true
]
