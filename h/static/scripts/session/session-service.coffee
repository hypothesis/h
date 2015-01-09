###*
# @ngdoc provider
# @name sessionProvider
# @property {Object} actions additional actions to mix into the resource.
# @property {Object} options additional options mix into resource actions.
# @description
# This class provides an angular $resource factory as an angular service
# for manipulating server-side sessions. It defines the REST-ish actions
# that return the state of the users session after modifying it through
# registration, authentication, or account management.
###
class SessionProvider
  actions: null
  options: null

  constructor: ->
    @actions = {}
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
  #     session.load(function (data) {
  #       var user = data.user;
  #       if(user && user.email == email) {
  #         navigator.id.completeAuthentication();
  #       } else {
  #         displayLoginForm();
  #       }
  #     });
  #   });
  ###
  $get: [
    '$http', '$q', '$resource', 'documentHelpers', 'flash', 'xsrf',
    ($http,   $q,   $resource,   documentHelpers,   flash,   xsrf) ->
      actions = {}
      provider = this

      prepare = (data, headersGetter) ->
        headersGetter()[$http.defaults.xsrfHeaderName] = xsrf.token
        return angular.toJson data

      process = (data, headersGetter) ->
        # Parse as json
        data = angular.fromJson data

        # Lift response data
        model = data.model or {}
        model.errors = data.errors
        model.reason = data.reason

        # Fire flash messages.
        for q, msgs of data.flash
          flash q, msgs

        xsrf.token = model.csrf

        # Return the model
        model

      for name, options of provider.actions
        actions[name] = angular.extend {}, options, @options
        actions[name].transformRequest = prepare
        actions[name].transformResponse = process

      endpoint = documentHelpers.absoluteURI('/app')
      $resource(endpoint, {}, actions)
  ]


angular.module('h.session')
.provider('session', SessionProvider)
