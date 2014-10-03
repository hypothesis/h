imports = [
  'ngResource'
  'h.identity'
  'h.helpers'
]


configure = [
  '$httpProvider', 'identityProvider',
  ($httpProvider,   identityProvider) ->
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
      'session',
      (session) ->
        session.logout({}).$promise
    ]

    identityProvider.requestAuthentication = [
      '$q', '$rootScope',
      ($q,   $rootScope) ->
        (authCheck = $q.defer()).promise.finally do ->
          $rootScope.$on 'auth', (event, err, data) ->
            if err then authCheck.reject err
            else authCheck.resolve data.csrf
    ]
]


angular.module('h.auth', imports, configure)
