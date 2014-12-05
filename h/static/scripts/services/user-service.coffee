# User authorization function for the Permissions plugin.
authorizeAction = (action, annotation, user) ->
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

class User
  _persona: undefined
  _checkingToken: false
  login: undefined
  logout: undefined

  this.$inject = ['annotator', 'documentHelpers']
  constructor:   ( annotator,   documentHelpers) ->
    {plugins} = annotator

    @login = (assertion, callbackFn) ->
      @_checkingToken = true

      # Configure the Auth plugin with the issued assertion as refresh token.
      annotator.addPlugin 'Auth',
        tokenUrl: documentHelpers.absoluteURI(
          "/api/token?assertion=#{assertion}")

      # Set the user from the token.
      plugins.Auth.withToken (token) =>
        @_checkingToken = false
        annotator.addPlugin 'Permissions',
          user: token.userId
          userAuthorize: authorizeAction
        @_persona = token.userId
        callbackFn()

    @logout = ->
      plugins.Auth?.element.removeData('annotator:headers')
      plugins.Auth?.destroy()
      delete plugins.Auth

      plugins.Permissions?.setUser(null)
      plugins.Permissions?.destroy()
      delete plugins.Permissions

      @_persona = null
      @_checkingToken = false

  checkingInProgress: -> @_checkingToken
  getPersona: -> @_persona
  noPersona: -> @_persona = null

angular.module('h')
.service('user', User)