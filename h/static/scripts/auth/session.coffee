imports = [
  'ngResource'
  'h.flash'
  'h.helpers.documentHelpers'
]


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


# Global because $resource doesn't support request interceptors, so a
# the default http request interceptor and the session resource interceptor
# need to share it.
csrfToken = null


# Class providing a server-side session resource.
#
# This class provides an angular $resource factory as an angular service
# for manipulating server-side sessions. It defines the authentication-oriented
# actions (such as 'login', 'register') as REST-ish actions on the session
# resource.
#
# @example Using the session with BrowserID
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
#
# Use the 'options' property of its provider to provide additional options
# to be mixed into the resource action definitions.
class SessionProvider
  options: null

  constructor: ->
    @options = {}

  $get: [
    '$q', '$resource', 'documentHelpers', 'flash',
    ($q,   $resource,   documentHelpers,   flash) ->
      actions = {}

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

        # Capture the cross site request forgery token without cookies.
        # If cookies are blocked this is our only way to get it.
        csrfToken = model.certificate

        # Return the model
        model

      for name, options of ACTION_OPTION
        actions[name] = angular.extend {}, options, @options
        actions[name].transformResponse = process

      endpoint = documentHelpers.absoluteURI('/app')
      $resource(endpoint, {}, actions)
  ]


configure = ['$httpProvider', ($httpProvider) ->
  defaults = $httpProvider.defaults

  # Use the Pyramid XSRF header name
  defaults.xsrfHeaderName = 'X-CSRF-Token'

  $httpProvider.interceptors.push ['documentHelpers', (documentHelpers) ->
    request: (config) ->
      endpoint = documentHelpers.absoluteURI('/app')
      if config.url.indexOf(endpoint) == 0
        # Set the cross site request forgery token
        cookieName = config.xsrfCookieName || defaults.xsrfCookieName
        headerName = config.xsrfHeaderName || defaults.xsrfHeaderName
        config.headers[headerName] ?= csrfToken
      config
  ]
]


angular.module('h.session', imports, configure)
.provider('session', SessionProvider)
