var angular = require('angular');

var SESSION_ACTIONS = [
  'login', 'logout', 'register', 'forgot_password',
  'reset_password', 'edit_profile', 'disable_user'
];


configure.$inject = ['$httpProvider', 'identityProvider', 'sessionProvider'];
function configure(   $httpProvider,   identityProvider,   sessionProvider) {
  // Pending authentication check
  var authCheck = null;

  // Use the Pyramid XSRF header name
  $httpProvider.defaults.xsrfHeaderName = 'X-CSRF-Token';

  identityProvider.checkAuthentication = [
    '$q', 'session', function($q, session) {
      authCheck = $q.defer();

      session.load().$promise
        .then(function (data) {
          if (data.userid) {
            authCheck.resolve(data.csrf);
          } else {
            authCheck.reject('no session');
          }
        })
        .catch(function () {
          authCheck.reject('request failure');
        });

      return authCheck.promise;
    }
  ];

  identityProvider.forgetAuthentication = [
    '$q', 'flash', 'session', function($q, flash, session) {
      return session.logout({}).$promise
        .then(function() {
          authCheck = $q.defer();
          authCheck.reject('no session');
          return null;
        })
        .catch(function(err) {
          flash.error('Sign out failed!');
          throw err;
        });
    }
  ];

  identityProvider.requestAuthentication = [
    '$q', '$rootScope', function($q, $rootScope) {
      return authCheck.promise.catch(function () {
        var authRequest = $q.defer();

        $rootScope.$on('auth', function(event, err, data) {
          if (err) {
            return authRequest.reject(err);
          } else {
            return authRequest.resolve(data.csrf);
          }
        });

        return authRequest.promise;
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

  for (var i = 0; i < SESSION_ACTIONS.length; i++) {
    var action = SESSION_ACTIONS[i];
    sessionProvider.actions[action] = {
      method: 'POST',
      params: {
        __formid__: action
      },
      withCredentials: true
    };
  }
}

angular.module('h')
  .value('xsrf', {token: null})
  .config(configure);
