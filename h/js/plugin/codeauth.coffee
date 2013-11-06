class Annotator.Plugin.CodeAuth extends Annotator.Plugin

  # These actions will be axposed on @annotator
  actions: [
    'loginWithUsernameAndPassword'
    'logout'
    'getLoginStatus'
    'registerUser'
  ]

  pluginInit: ->
    for i in @actions
      @annotator[i] = this[i]
            
    addEventListener "annotatorReady", => @annotator.panel
      .bind('onLogin', (ctx, user) =>
        if @_pendingLogin?
          @_pendingLogin?.resolve()
          delete @_pendingLogin
        else
          event = document.createEvent "UIEvents"
          event.initUIEvent "annotatorLogin", false, false, window, 0
          event.user = user
          window.dispatchEvent event
      )

      .bind('onLoginFailed', (ctx, data) =>
        @_pendingLogin?.reject data
        delete @_pendingLogin
      )

      .bind('onLogout', =>
        if @_pendingLogout?
          @_pendingLogout.resolve()
          delete @_pendingLogout
        else
          event = document.createEvent "UIEvents"
          event.initUIEvent "annotatorLogout", false, false, window, 0
          window.dispatchEvent event
      )

      .bind('onRegisterFailed', (ctx, data) =>
        @_pendingRegister?.reject data
        delete @_pendingRegister
      )

      .bind('onRegister', (ctx, user) =>
        if @_pendingRegister?
          @_pendingRegister?.resolve user
          delete @_pendingRegister
        else
          event = document.createEvent "UIEvents"
          event.initUIEvent "annotatorRegister", false, false, window, 0
          event.user = user
          window.dispatchEvent event
      )

  # Public API to trigger a login
  loginWithUsernameAndPassword: (username, password) =>
    @_pendingLogin = @annotator.constructor.$.Deferred()
    if @annotator.panel?
      @annotator.panel.notify method: "login", params:
        username: username
        password: password
    else
      @pendingLogin.reject "Panel connection is not yet available."
    @_pendingLogin

  # Public API to trigger a logout
  logout: =>
    @_pendingLogout = @annotator.constructor.$.Deferred()
    if @annotator.panel?
      @annotator.panel.notify method: "logout"
    else
      @pendingLogout.reject "Panel connection is not yet available."
    @_pendingLogout

  # Public API to get login status
  getLoginStatus: =>
    result = @annotator.constructor.$.Deferred()
    if @annotator.panel?
      @annotator.panel.call
        method: "getLoginStatus"
        success: (data) ->
          result.resolve data
        error: (problem) -> result.reject problem
    else
      result.reject "Panel connection is not yet available."
    result

  # Public API to register a user
  registerUser: (username, email, password) =>
    @_pendingRegister = @annotator.constructor.$.Deferred()
    if @annotator.panel?
      @annotator.panel.notify method: "registerUser", params:
        username: username
        email: email
        password: password
    else
      @pendingRegister.reject "Panel connection is not yet available."
    @_pendingRegister
