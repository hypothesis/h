LOGIN_REQUEST = 'login'
LOGOUT_REQUEST = 'logout'
INITIAL_REQUEST = 'initial'

pendingRequests =
  login: []
  logout: []
  initial: []

resolvePendingRequests = (requestType, user) ->
  for request in pendingRequests[requestType]
    request.resolve user if request.resolve?
  pendingRequests[requestType] = []

rejectPendingRequests = (requestType, reason) ->
  for request in pendingRequests[requestType]
    request.reject reason if request.reject?
  pendingRequests[requestType] = []


class Auth
  _checkingToken: false

  login: null
  logout: null
  getInitialUser: null
  user: null

  this.$inject = ['$location', '$q',
                  'annotator', 'documentHelpers', 'identity']
  constructor:   ( $location,   $q,
                   annotator,   documentHelpers,   identity) ->
    {plugins} = annotator

    @login = ->
      oncancel = ->
        rejectPendingRequests LOGIN_REQUEST, null

      deferred = $q.defer()
      pendingRequests[LOGIN_REQUEST].push deferred
      identity.request({oncancel})

      deferred.promise

    @logout = ->
      deferred = $q.defer()
      identity.logout()
      pendingRequests[LOGOUT_REQUEST].push deferred

      deferred.promise

    @getInitialUser = ->
      deferred = $q.defer()
      pendingRequests[INITIAL_REQUEST].push deferred

      deferred.promise

    onlogin = (assertion) =>
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
          userAuthorize: @permits
        @user = token.userId
        resolvePendingRequests INITIAL_REQUEST, @user
        resolvePendingRequests LOGIN_REQUEST, @user

    onlogout = =>
      plugins.Auth?.element.removeData('annotator:headers')
      plugins.Auth?.destroy()
      delete plugins.Auth

      plugins.Permissions?.setUser(null)
      plugins.Permissions?.destroy()
      delete plugins.Permissions

      @user = null
      @_checkingToken = false

      resolvePendingRequests LOGOUT_REQUEST, @user

    onready = =>
      if not @_checkingToken
        rejectPendingRequests INITIAL_REQUEST, null

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
