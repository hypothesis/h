var angular = require('angular');

var SESSION_ACTIONS = ['login', 'logout', 'register', 'forgot_password',
  'reset_password', 'edit_profile', 'disable_user'];

var configure = [
  '$httpProvider', 'identityProvider', 'sessionProvider',
  function($httpProvider, identityProvider, sessionProvider) {
    var action;
    var authCheck;
    authCheck = null;
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRF-Token';
    identityProvider.checkAuthentication = [
      '$q', 'session',
      function($q, session) {
        return (authCheck = $q.defer()).promise.then((function() {
          return session.load().$promise.then(function(data) {
            if (data.userid) {
              return authCheck.resolve(data.csrf);
            } else {
              return authCheck.reject('no session');
            }
          }, function() {
            return authCheck.reject('request failure');
          });
        })());
      }
    ];
    identityProvider.forgetAuthentication = [
      '$q', 'flash', 'session',
      function($q, flash, session) {
        return session.logout({}).$promise.then(function() {
          authCheck = $q.defer();
          authCheck.reject('no session');
          return null;
        }).catch(function(err) {
          flash.error('Sign out failed!');
          throw err;
        });
      }
    ];
    identityProvider.requestAuthentication = [
      '$q', '$rootScope',
      function($q, $rootScope) {
        return authCheck.promise.catch(function() {
          var authRequest;
          return (authRequest = $q.defer()).promise.finally((function() {
            return $rootScope.$on('auth', function(event, err, data) {
              if (err) {
                return authRequest.reject(err);
              } else {
                return authRequest.resolve(data.csrf);
              }
            });
          })());
        });
      }
    ];
    sessionProvider.actions.load = {
      method: 'GET',
      withCredentials: true
    };
    sessionProvider.actions.profile = {
      method: 'GET',
      params: {
        __formid__: 'profile'
      },
      withCredentials: true
    };
    var results = [];
    for (var i = 0; i < SESSION_ACTIONS.length; i++) {
      action = SESSION_ACTIONS[i];
      results.push(sessionProvider.actions[action] = {
        method: 'POST',
        params: {
          __formid__: action
        },
        withCredentials: true
      });
    }
    return results;
  }
];

angular.module('h').value('xsrf', {
  token: null
}).config(configure);
