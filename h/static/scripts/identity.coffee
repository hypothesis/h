###*
# @ngdoc provider
# @name identityProvider

# @property {function} checkAuthentication A function to check for an
# authenticated user. It is expected to return the promise of an authorization
# grant if the user has authorized signing in to the requesting application.
# The function arguments are injected.
#
# @property {function} forgetAuthentication A function to forget the current
# authentication. The return value, if any, will be resolved as a promise
# before the identity service fires logout callbacks. The identity provider
# should ensure any sessions are cleared. The function arguments are injected.
#
# @property {function} requestAuthentication A function to request that the
# the user begin authenticating. It is expected to return the promise of an
# authorization grant once the user has authenticated and authorized signing
# in to the requesting application. The function arguments are injected.
#
# @description
# The `identityProvider` is used to configure functions that fulfill
# identity authorization state management requests. It allows applications
# that perform authentication to export their authentication responding to
# identity authorization requests from clients consuming the
# {@link h.identity:identity identity} service.
#
# An application wishing to export an identity provider should override all
# of the public methods of this provider. The all are expected to return a
# promise of an authorization grant that may be the null value or an object.
# If it is an object, it is considered a valid grant if it contains the keys
# ``userid`` and ``certificate``.
###
identityProvider = ->
  checkAuthentication: ['$q', ($q) ->
    $q.reject 'Not implemented idenityProvider#checkAuthentication.'
  ]

  forgetAuthentication: ['$q', ($q) ->
    $q.reject 'Not implemented idenityProvider#forgetAuthentication.'
  ]

  requestAuthentication: ['$q', ($q) ->
    $q.reject 'Not implemented idenityProvider#requestAuthentication.'
  ]

  ###*
  # @ngdoc service
  # @name identity
  # @description
  # This service is used by a client application to request authorization for
  # the user identity (login), relinquish authorization (logout), and set
  # callbacks to observe identity changes.
  #
  # See https://developer.mozilla.org/en-US/docs/Web/API/navigator.id
  ###
  $get: [
    '$injector', '$q',
    ($injector,   $q) ->
      provider = this
      onlogin = null
      onlogout = null

      ###*
      # @ngdoc method
      # @name identity#logout
      # @description
      # https://developer.mozilla.org/en-US/docs/Web/API/navigator.id.logout
      ###
      logout: ->
        result = $injector.invoke(provider.forgetAuthentication, provider)
        $q.when(result).finally(onlogout)

      ###*
      # @ngdoc method
      # @name identity#request
      # @description
      # https://developer.mozilla.org/en-US/docs/Web/API/navigator.id.request
      ###
      request: (options={}) ->
        {oncancel} = options
        result = $injector.invoke(provider.requestAuthentication, provider)
        $q.when(result).then(onlogin, oncancel)

      ###*
      # @ngdoc method
      # @name identity#watch
      # @description
      # https://developer.mozilla.org/en-US/docs/Web/API/navigator.id.watch
      ###
      watch: (options) ->
        {loggedInUser, onlogin, onlogout, onready} = options
        result = $injector.invoke(provider.checkAuthentication, provider)
        $q.when(result).then(onlogin).finally(-> onready?())
  ]


angular.module('h.identity', [])
.provider('identity', identityProvider)
