imports = [
  'h.session'
]


identityFactory = [
  '$rootScope', 'session',
  ($rootScope,   session) ->
    loggedInUser = undefined

    onlogin = null
    onlogout = null
    onmatch = null

    $rootScope.$on 'session', (event, session) ->
      # Get the userid and convert it to the persona format.
      persona = session.userid?.replace(/^acct:/, '') or null

      # Fire callbacks as appropriate.
      # Consult the state matrix in the `navigator.id.watch` documentation.
      # https://developer.mozilla.org/en-US/docs/Web/API/navigator.id.watch
      if loggedInUser is null
        if persona
          loggedInUser = persona
          onlogin?(session.csrf)
        else
          onmatch?()
      else if loggedInUser
        if persona
          if loggedInUser is persona
            onmatch?()
          else
            loggedInUser = persona
            onlogin?(session.csrf)
        else
          loggedInUser = null
          onlogout?()
      else
        if persona
          loggedInUser = persona
          onlogin?(session.csrf)
        else
          loggedInUser = null
          onlogout?()

    logout: ->
      session.logout({}).$promise.then ->
        $rootScope.$emit 'session', {}

    request: ->
      $rootScope.$broadcast 'authorize'

    watch: (options) ->
      {loggedInUser, onlogin, onlogout, onmatch} = options
      session.load().$promise.then (data) -> $rootScope.$emit 'session', data
]


angular.module('h.identity', imports)
.factory('identity', identityFactory)
