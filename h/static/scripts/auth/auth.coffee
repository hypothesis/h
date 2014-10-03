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
        (authCheck = $q.defer())
        .promise.then do ->
          session.load().$promise.then (data) ->
            authCheck.resolve
              certificate: data.csrf
              userid: data.userid
    ]

    identityProvider.forgetAuthentication = [
      'session',
      (session) ->
        session.logout({}).$promise
    ]

    identityProvider.requestAuthentication = [
      '$q', '$rootScope',
      ($q,   $rootScope) ->
        if authCheck then authCheck.reject()
        (authCheck = $q.defer())
        .promise.finally do ->
          $rootScope.$on 'auth', (event, err, data) ->
            if err
              authCheck.reject(err)
            else
              authCheck.resolve
                certificate: data.csrf
                userid: data.userid
    ]
]


angular.module('h.auth', imports, configure)
