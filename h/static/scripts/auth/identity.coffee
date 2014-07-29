imports = [
  'h.helpers'
  'h.session'
]


identityFactory = [
  '$rootScope', 'baseURI', 'session',
  ($rootScope,   baseURI,   session) ->
    loggedInUser = undefined

    onlogin = null
    onlogout = null
    onmatch = null

    $rootScope.session = session

    $rootScope.$watch 'session.$promise', (promise) ->
      # Wait for any pending action to resolve.
      promise.finally ->
        # Get the userid and convert it to the persona format.
        persona = session.userid?.replace(/^acct:/, '') or null

        # Fire callbacks as appropriate.
        # Consult the state matrix in the `navigator.id.watch` documentation.
        # https://developer.mozilla.org/en-US/docs/Web/API/navigator.id.watch
        if loggedInUser is null
          if persona
            loggedInUser = persona
            onlogin?(session.csrf_token)
          else
            onmatch?()
        else if loggedInUser
          if persona
            if loggedInUser is persona
              onmatch?()
            else
              loggedInUser = persona
              onlogin?(session.csrf_token)
          else
            loggedInUser = null
            onlogout?()
        else
          if persona
            loggedInUser = persona
            onlogin?(session.csrf_token)
          else
            loggedInUser = null
            onlogout?()

    logout: ->
      # Clear the session but preserve its identity and give it a new promise.
      $promise = session.$logout()
      $resolved = false
      angular.copy({$promise, $resolved}, session)

    request: ->
      $rootScope.$broadcast 'authorize'

    watch: (options) ->
      {loggedInUser, onlogin, onlogout, onmatch} = options
]


angular.module('h.identity', imports)
.factory('identity', identityFactory)
