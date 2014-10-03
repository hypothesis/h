ACTION = [
  'login'
  'logout'
  'register'
  'forgot'
  'activate'
  'edit_profile'
  'disable_user'
]

ACTION_OPTION =
  load:
    method: 'GET'
    withCredentials: true

for action in ACTION
  ACTION_OPTION[action] =
    method: 'POST'
    params:
      __formid__: action
    withCredentials: true


###*
# @ngdoc provider
# @name sessionProvider
# @property {Object} options additional options mix into resource actions.
# @description
# This class provides an angular $resource factory as an angular service
# for manipulating server-side sessions. It defines the REST-ish actions
# that return the state of the users session after modifying it through
# registration, authentication, or account management.
###
class SessionProvider
  options: null

  constructor: ->
    @options = {}

  ###*
  # @ngdoc service
  # @name session
  # @description
  # An angular resource factory for sessions. See the documentation for
  # {@link sessionProvider sessionProvider} for ways to configure the
  # resource.
  #
  # @example
  # Using the session with BrowserID.
  #
  #   navigator.id.beginAuthentication(function (email) {
  #     session.load({email: email}, function (session) {
  #       var user = session.user;
  #       if(user && user.email == email) {
  #         navigator.id.completeAuthentication();
  #       } else {
  #         displayLoginForm();
  #       }
  #     });
  #   });
  ###
  $get: [
    '$http', '$q', '$resource', 'documentHelpers', 'flash',
    ($http,   $q,   $resource,   documentHelpers,   flash) ->
      actions = {}
      provider = this

      # Capture the state of the cross site request forgery token.
      # If cookies are blocked this is our only way to get it.
      xsrfToken = null

      prepare = (data, headersGetter) ->
        if xsrfToken
          headers = headersGetter()
          headers[$http.defaults.xsrfHeaderName] = xsrfToken
        return angular.toJson data

      process = (data, headersGetter) ->
        # Parse as json
        data = angular.fromJson data

        # Lift response data
        model = data.model
        model.errors = data.errors
        model.reason = data.reason

        # Fire flash messages.
        for q, msgs of data.flash
          flash q, msgs

        xsrfToken = model.csrf

        # Return the model
        model

      for name, options of ACTION_OPTION
        actions[name] = angular.extend {}, options, @options
        actions[name].transformRequest = prepare
        actions[name].transformResponse = process

      endpoint = documentHelpers.absoluteURI('/app')
      $resource(endpoint, {}, actions)
  ]


angular.module('h.auth')
.provider('session', SessionProvider)
