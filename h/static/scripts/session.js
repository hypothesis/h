'use strict';

var angular = require('angular');

var ACCOUNT_ACTIONS = [
  ['login', 'POST'],
  ['logout', 'POST'],
  ['register', 'POST'],
  ['forgot_password', 'POST'],
  ['reset_password', 'POST'],
  ['profile', 'GET'],
  ['edit_profile', 'POST'],
  ['disable_user', 'POST']
];

function sessionActions(options) {
  var actions = {};

  // These map directly to views in `h.accounts`, and all have a similar form:
  for (var i = 0, len = ACCOUNT_ACTIONS.length; i < len; i++) {
    var name = ACCOUNT_ACTIONS[i][0];
    var method = ACCOUNT_ACTIONS[i][1];
    actions[name] = {
      method: method,
      params: {
        __formid__: name
      }
    };
  }

  // Finally, add a simple method for getting the current session state
  actions.load = {method: 'GET'};

  if (typeof options !== 'undefined') {
    for (var act in actions) {
      for (var opt in options) {
        actions[act][opt] = options[opt];
      }
    }
  }

  return actions;
}


/**
 * @ngdoc service
 * @name session
 * @description
 * Access to the application session and account actions. This service gives
 * other parts of the application access to parts of the server-side session
 * state (such as current authenticated userid, CSRF token, etc.).
 *
 * In addition, this service also provides helper methods for mutating the
 * session state, by, e.g. logging in, logging out, etc.
 */
 // TODO: Move accounts data management (e.g. profile, edit_profile,
 // disable_user, etc) into another module with another route.
session.$inject = ['$document', '$http', '$resource', 'flash', 'xsrf'];
function session(   $document,   $http,   $resource,   flash,   xsrf) {
  var actions = sessionActions({
    transformRequest: prepare,
    transformResponse: process,
    withCredentials: true
  });
  var base = $document.prop('baseURI');
  var endpoint = new URL('/app', base).href;
  var resource = $resource(endpoint, {}, actions);

  // Blank inital model state
  resource.state = {};

  function prepare(data, headersGetter) {
    headersGetter()[$http.defaults.xsrfHeaderName] = xsrf.token;
    return angular.toJson(data);
  }

  function process(data, headersGetter) {
    // Parse as json
    data = angular.fromJson(data);

    // Lift response data
    var model = data.model || {};
    if (typeof data.errors !== 'undefined') {
      model.errors = data.errors;
    }
    if (typeof data.reason !== 'undefined') {
      model.reason = data.reason;
    }

    // Fire flash messages.
    for (var type in data.flash) {
      if (data.flash.hasOwnProperty(type)) {
        var msgs = data.flash[type];
        for (var i = 0, len = msgs.length; i < len; i++) {
          flash[type](msgs[i]);
        }
      }
    }

    xsrf.token = model.csrf;
    angular.copy(model, resource.state);

    // Return the model
    return model;
  }

  return resource;
}

module.exports = session;
