###*
# @ngdoc provider
# @name identityProvider

# @property {function} checkAuthorization A function to check for a current
# authorization grant. It is expected to return the promise of a grant.
#
# @property {function} forgetAuthorization A function to forget the current
# authorization grant. It is expected to return the promise of a grant. If
# the user is successfully logged out the grant should be null or invalid.
#
# @property {function} requestAuthorization A function to request that the
# the client begin authenticated the current user. It is expected to return the
# promise of an authorization grant once the user has authenticated and
# authorized signing in to the requesting application.
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
  checkAuthorization: ['$q', ($q) ->
    $q.reject 'Not implemented idenityProvider#checkAuthorization.'
  ]

  forgetAuthorization: ['$q', ($q) ->
    $q.reject 'Not implemented idenityProvider#forgetAuthorization.'
  ]

  requestAuthorization: ['$q', ($q) ->
    $q.reject 'Not implemented idenityProvider#requestAuthorization.'
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
      loggedInUser = undefined
      oncancel = null
      onlogin = null
      onlogout = null
      onmatch = null

      invokeCallbacks = (grant={}) ->
        {userid, certificate} = grant
        userid or= null
        # Fire callbacks as appropriate.
        # Consult the state matrix in the `navigator.id.watch` documentation.
        # https://developer.mozilla.org/en-US/docs/Web/API/navigator.id.watch
        if loggedInUser is null
          if userid
            loggedInUser = userid
            onlogin?(certificate)
          else
            onmatch?()
        else if loggedInUser
          if userid
            if loggedInUser is userid
              onmatch?()
            else
              loggedInUser = userid
              onlogin?(certificate)
          else
            loggedInUser = null
            onlogout?()
        else
          if userid
            loggedInUser = userid
            onlogin?(certificate)
          else
            loggedInUser = null
            onlogout?()

      ###*
      # @ngdoc method
      # @name identity#logout
      # @description
      # https://developer.mozilla.org/en-US/docs/Web/API/navigator.id.logout
      ###
      logout: ->
        result = $injector.invoke(provider.forgetAuthorization, provider)
        $q.when(result).finally(-> onlogout?())

      ###*
      # @ngdoc method
      # @name identity#request
      # @description
      # https://developer.mozilla.org/en-US/docs/Web/API/navigator.id.request
      ###
      request: (options={}) ->
        {oncancel} = options
        result = $injector.invoke(provider.requestAuthorization, provider)
        $q.when(result).then(invokeCallbacks, oncancel)

      ###*
      # @ngdoc method
      # @name identity#watch
      # @description
      # https://developer.mozilla.org/en-US/docs/Web/API/navigator.id.watch
      ###
      watch: (options) ->
        {loggedInUser, onlogin, onlogout, onmatch} = options
        result = $injector.invoke(provider.checkAuthorization, provider)
        result.then(invokeCallbacks)
  ]


angular.module('h.identity', [])
.provider('identity', identityProvider)
