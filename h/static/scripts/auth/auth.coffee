imports = [
  'ngResource'
  'h.identity'
  'h.helpers'
]


configure = ['$httpProvider', 'identityProvider', ($httpProvider, identityProvider) ->
  defaults = $httpProvider.defaults

  # Use the Pyramid XSRF header name
  defaults.xsrfHeaderName = 'X-CSRF-Token'

  $httpProvider.interceptors.push ['documentHelpers', (documentHelpers) ->
    request: (config) ->
      endpoint = documentHelpers.absoluteURI('/app')
      if config.url.indexOf(endpoint) == 0
        # Set the cross site request forgery token
        cookieName = config.xsrfCookieName || defaults.xsrfCookieName
        headerName = config.xsrfHeaderName || defaults.xsrfHeaderName
        config.headers[headerName] ?= csrfToken
      config
  ]

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
