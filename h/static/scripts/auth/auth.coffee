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
        session.load().$promise
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
        $rootScope.$on 'session', (event, data) -> deferred.resolve data
        deferred.promise
    ]
]


angular.module('h.auth', imports, configure)
