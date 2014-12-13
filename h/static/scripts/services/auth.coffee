class Auth

  this.$inject = ['$location', '$rootScope',
                  'annotator', 'documentHelpers', 'identity']
  constructor:   ( $location,   $rootScope,
                   annotator,   documentHelpers,   identity) ->
    {plugins} = annotator
    _checkingToken = false
    @user = undefined

    onlogin = (assertion) =>
      _checkingToken = true

      # Configure the Auth plugin with the issued assertion as refresh token.
      annotator.addPlugin 'Auth',
        tokenUrl: documentHelpers.absoluteURI(
          "/api/token?assertion=#{assertion}")

      # Set the user from the token.
      plugins.Auth.withToken (token) =>
        _checkingToken = false
        annotator.addPlugin 'Permissions',
          user: token.userId
          userAuthorize: @permits
        @user = token.userId
        $rootScope.$apply()

    onlogout = =>
      plugins.Auth?.element.removeData('annotator:headers')
      plugins.Auth?.destroy()
      delete plugins.Auth

      plugins.Permissions?.setUser(null)
      plugins.Permissions?.destroy()
      delete plugins.Permissions

      @user = null
      _checkingToken = false

    onready = =>
      if @user is undefined and not _checkingToken
        @user = null

    identity.watch {onlogin, onlogout, onready}


  # User authorization function for the Permissions plugin.
  permits: (action, annotation, user) ->
    if annotation.permissions
      tokens = annotation.permissions[action] || []

      if tokens.length == 0
        # Empty or missing tokens array: only admin can perform action.
        return false

      for token in tokens
        if user == token
          return true
        if token == 'group:__world__'
          return true

      # No tokens matched: action should not be performed.
      return false

    # Coarse-grained authorization
    else if annotation.user
      return user and user == annotation.user

    # No authorization info on annotation: free-for-all!
    true

angular.module('h')
.service('auth', Auth)
