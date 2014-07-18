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

      _process = (response) ->
        data = response.data
        model = data.model

        # bw compat
        if angular.isObject(data.persona)
          persona = data.persona
          data.persona = "acct:#{persona.username}@#{persona.provider}"
          data.personas = for persona in data.personas
            "acct:#{persona.username}@#{persona.provider}"
        # end bw compat

        # Fire flash messages.
        for q, msgs of data.flash
          flash q, msgs

        # Capture the cross site request forgery token without cookies.
        # If cookies are blocked this is our only way to get it.
        csrfToken = model.csrf
        delete model.csrf

        # Lift the model object so it becomes the response data.

        # Return the response or a rejected response.
        if data.status is 'failure'
          $q.reject(data)
        else
          model

      for name, options of ACTION_OPTION
        actions[name] = angular.extend {}, options, @options
        actions[name].interceptor =
          response: _process
          responseError: _process

      $resource("#{baseURI}app", {}, actions).load()
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
