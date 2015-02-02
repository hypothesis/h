###*
# @ngdoc service
# @name  Auth
#
# @description
# The 'Auth' service exposes the currently logged in user for other components,
# configures the Annotator.Auth plugin according to the login/logout events
# and provides a method for permitting a certain operation for a user with a
# given annotation
###
class Auth

  this.$inject = ['$document', '$http', '$location', '$rootScope',
                  'annotator', 'identity']
  constructor:   ( $document,   $http,   $location,   $rootScope,
                   annotator,   identity) ->
    {plugins} = annotator
    _checkingToken = false
    @user = undefined

    # Fired when the identity-service successfully requests authentication.
    # Sets up the Annotator.Auth plugin instance and the auth.user property.
    # It sets a flag between that time period to indicate that the token is
    # being checked.
    onlogin = (assertion) =>
      _checkingToken = true

      base = $document.prop('baseURI')
      tokenUrl = new URL("/api/token?assertion=#{assertion}", base).href

      # Configure the Auth plugin with the issued assertion as refresh token.
      annotator.addPlugin 'Auth', tokenUrl: tokenUrl

      # Set the user from the token.
      plugins.Auth.withToken (payload) =>
        _checkingToken = false
        @user = payload.userId
        token = plugins.Auth.token
        $http.defaults.headers.common['X-Annotator-Auth-Token'] = token
        $rootScope.$apply()

    # Fired when the identity-service forgets authentication.
    # Destroys the Annotator.Auth plugin instance and sets
    # the user to null.
    onlogout = =>
      plugins.Auth?.destroy()
      delete plugins.Auth
      delete $http.defaults.headers.common['X-Annotator-Auth-Token']

      @user = null
      _checkingToken = false

    # Fired after the identity-service requested authentication (both after
    # a failed or succeeded request). It detects if the first login request
    # has failed and if yes, it sets the user value to null. (Otherwise the
    # onlogin method would set it to userId)
    onready = =>
      if @user is undefined and not _checkingToken
        @user = null

    identity.watch {onlogin, onlogout, onready}


angular.module('h')
.service('auth', Auth)
