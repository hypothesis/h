imports = [
  'ngResource'
  'h.flash'
  'h.helpers'
]


ACTION = [
  'login'
  'logout'
  'register'
  'forgot'
  'activate'
  'edit_profile'
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
    '$q', '$resource', 'baseURI', 'flash',
    ($q,   $resource,   baseURI,   flash) ->
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
        csrfToken = model.csrf
        delete model.csrf

        # Return the model
        model

      for name, options of ACTION_OPTION
        actions[name] = angular.extend {}, options, @options
        actions[name].transformResponse = process

      $resource("#{baseURI}app", {}, actions).load()
  ]

# Function providing a server-side session resource.
#
# This function provides an angular $resource factory
# for manipulating server-side account-profile settings. It defines the
# actions (such as 'login', 'register') as REST-ish actions
profileProvider = [
  '$q', '$resource', 'baseURI',
  ($q,   $resource,   baseURI) ->
    defaults =
      email: ""
      password: ""

    actions =
      edit_profile:
        method: 'POST'
        params:
          __formid__: "edit_profile"
        withCredentials: true
      disable_user:
        method: 'POST'
        params:
          __formid__: "disable_user"
        withCredentials: true

    $resource("#{baseURI}app", {}, actions)
]


configure = ['$httpProvider', ($httpProvider) ->
  defaults = $httpProvider.defaults

  # Use the Pyramid XSRF header name
  defaults.xsrfHeaderName = 'X-CSRF-Token'

  $httpProvider.interceptors.push ['baseURI', (baseURI) ->
    request: (config) ->
      if config.url.match("#{baseURI}app")?.index == 0
        # Set the cross site request forgery token
        cookieName = config.xsrfCookieName || defaults.xsrfCookieName
        headerName = config.xsrfHeaderName || defaults.xsrfHeaderName
        config.headers[headerName] ?= csrfToken
      config
  ]
]


angular.module('h.session', imports, configure)
.provider('session', SessionProvider)
.factory('profile', profileProvider)
