angular = require('angular')


class AuthAppController
  this.$inject = ['$location', '$scope', '$timeout', '$window', 'session']
  constructor:   ( $location,   $scope,   $timeout,   $window,   session ) ->
    onlogin = ->
      $window.location.href = '/stream'

    $scope.account = {}
    $scope.model = {}

    $scope.account.tab = $location.path().split('/')[1]

    $scope.$on 'auth', (event, err, data) ->
      if data?.userid
        $timeout onlogin, 1000

    $scope.$watch 'account.tab', (tab, old) ->
      unless tab is old then $location.path("/#{tab}")

    # TODO: We should be calling identity.beginProvisioning() here in order to
    # move toward become a federated BrowserID provider.
    session.load (data) ->
      if data.userid then onlogin()


class AuthPageController
  this.$inject = ['$routeParams', '$scope']
  constructor:   ( $routeParams,   $scope ) ->
    $scope.model.code = $routeParams.code
    $scope.hasActivationCode = !!$routeParams.code


configure = [
  '$httpProvider', '$locationProvider', '$routeProvider'
  (
   $httpProvider,   $locationProvider,   $routeProvider
  ) ->
    # Use the Pyramid XSRF header name
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRF-Token'

    $locationProvider.html5Mode(true)

    $routeProvider.when '/login',
      controller: 'AuthPageController'
      templateUrl: 'auth.html'
    $routeProvider.when '/register',
      controller: 'AuthPageController'
      templateUrl: 'auth.html'
    $routeProvider.when '/forgot_password',
      controller: 'AuthPageController'
      templateUrl: 'auth.html'
    $routeProvider.when '/reset_password/:code?',
      controller: 'AuthPageController'
      templateUrl: 'auth.html'
]


angular.module('h')
.config(configure)
.controller('AuthAppController', AuthAppController)
.controller('AuthPageController', AuthPageController)

require('./account-controller')
require('./auth-controller')
