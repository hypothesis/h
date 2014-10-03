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

    identityProvider.checkAuthorization = [
      'session',
      (session) ->
        session.load().$promise.then (data) ->
          certificate: data.csrf
          userid: data.userid
    ]

    identityProvider.forgetAuthorization = [
      'session',
      (session) ->
        session.logout({}).$promise
    ]

    identityProvider.requestAuthorization = [
      '$q', '$rootScope',
      ($q,   $rootScope) ->
        deferred = $q.defer()

        $rootScope.$on 'session', (event, data) ->
          deferred.resolve
            certificate: data.csrf
            userid: data.userid

        deferred.promise
    ]
]


angular.module('h.auth', imports, configure)
