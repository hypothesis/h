imports = [
  'ngResource'
  'h.helpers'
]


# bw compat
sessionPersonaInterceptor = (response) ->
  data = response.data
  if angular.isObject(data.persona)
    persona = data.persona
    data.persona = "acct:#{persona.username}@#{persona.provider}"
    data.personas = for persona in data.personas
      "acct:#{persona.username}@#{persona.provider}"
  response

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
    interceptor:
      response: sessionPersonaInterceptor

for action in ACTION
  ACTION_OPTION[action] =
    method: 'POST'
    params:
      __formid__: action
    withCredentials: true
    interceptor:
      response: sessionPersonaInterceptor


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
    '$resource', 'baseURI'
    ($resource,   baseURI) ->
      actions = {}

      for name, options of ACTION_OPTION
        actions[name] = angular.extend {}, options, @options

      model = $resource("#{baseURI}app", {}, actions).load()
  ]


angular.module('h.session', imports)
.provider('session', SessionProvider)
