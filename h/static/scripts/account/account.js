var angular = require('angular');

// @ngInject
function AuthAppController($location, $scope, $timeout, $window, session) {
  function onlogin() {
    window.location.href = '/stream';
  };

  $scope.account = {};
  $scope.model = {};
  $scope.account.tab = $location.path().split('/')[1];

  $scope.$on('auth', function(event, err, data) {
    if (data != null ? data.userid : void 0) {
      $timeout(onlogin, 1000);
    }
  });

  $scope.$watch('account.tab', function(tab, old) {
    if (tab !== old) {
      $location.path('/' + tab);
    }
  });

  // TODO: We should be calling identity.beginProvisioning() here in order to
  // move toward become a federated BrowserID provider.
  session.load(function(data) {
    if (data.userid) {
      onlogin();
    }
  });
}


// @ngInject
function AuthPageController($routeParams, $scope) {
  $scope.model.code = $routeParams.code;
  $scope.hasActivationCode = !!$routeParams.code;
}


// @ngInject
function configure($httpProvider, $locationProvider, $routeProvider) {
  // Use the Pyramid XSRF header name
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
  $routeProvider.when('/reset_password/:code?', {
    controller: 'AuthPageController',
    templateUrl: 'auth.html'
  });
}

angular.module('h')
  .config(configure)
  .controller('AuthAppController', AuthAppController)
  .controller('AuthPageController', AuthPageController);

require('./account-controller');
require('./auth-controller');
