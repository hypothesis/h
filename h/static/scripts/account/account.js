var angular = require('angular');

var AuthAppController = (function() {
  AuthAppController.$inject = ['$location', '$scope', '$timeout', '$window',
    'session'];

  function AuthAppController($location, $scope, $timeout, $window, session) {
    var onlogin;
    onlogin = function() {
      return $window.location.href = '/stream';
    };
    $scope.account = {};
    $scope.model = {};
    $scope.account.tab = $location.path().split('/')[1];
    $scope.$on('auth', function(event, err, data) {
      if (data != null ? data.userid : void 0) {
        return $timeout(onlogin, 1000);
      }
    });
    $scope.$watch('account.tab', function(tab, old) {
      if (tab !== old) {
        return $location.path('/' + tab);
      }
    });
    session.load(function(data) {
      if (data.userid) {
        return onlogin();
      }
    });
  }

  return AuthAppController;

})();

var AuthPageController = (function() {
  AuthPageController.$inject = ['$routeParams', '$scope'];

  function AuthPageController($routeParams, $scope) {
    $scope.model.code = $routeParams.code;
    $scope.hasActivationCode = !!$routeParams.code;
  }

  return AuthPageController;

})();

var configure = [
  '$httpProvider', '$locationProvider', '$routeProvider',
  function($httpProvider, $locationProvider, $routeProvider) {
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRF-Token';
    $locationProvider.html5Mode(true);
    $routeProvider.when('/login', {
      controller: 'AuthPageController',
      templateUrl: 'auth.html'
    });
    $routeProvider.when('/register', {
      controller: 'AuthPageController',
      templateUrl: 'auth.html'
    });
    $routeProvider.when('/forgot_password', {
      controller: 'AuthPageController',
      templateUrl: 'auth.html'
    });
    return $routeProvider.when('/reset_password/:code?', {
      controller: 'AuthPageController',
      templateUrl: 'auth.html'
    });
  }
];

angular.module('h')
  .config(configure)
  .controller('AuthAppController', AuthAppController)
  .controller('AuthPageController', AuthPageController);

require('./account-controller');

require('./auth-controller');
