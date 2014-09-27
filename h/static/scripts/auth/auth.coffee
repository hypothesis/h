imports = [
  'h.identity'
  'h.session'
]


class AuthController
  this.$inject = ['$scope', '$timeout', 'flash', 'session', 'formHelpers']
  constructor:   ( $scope,   $timeout,   flash,   session,   formHelpers ) ->
    timeout = null

    success = (data) ->
      if $scope.tab is 'forgot' then $scope.tab = 'activate'
      if data.userid then $scope.$emit 'session', data
      $scope.model = null
      $scope.form?.$setPristine()

    failure = (form, response) ->
      {errors, reason} = response.data
      formHelpers.applyValidationErrors(form, errors, reason)

    this.submit = (form) ->
      delete form.responseErrorMessage
      form.$setValidity('response', true)

      return unless form.$valid

      $scope.$broadcast 'formState', form.$name, 'loading'
      session[form.$name] $scope.model, success,
        angular.bind(this, failure, form)
      .$promise.finally -> $scope.$broadcast 'formState', form.$name, ''

    $scope.model = null
    $scope.tab = 'login'

    $scope.$on '$destroy', ->
      if timeout
        $timeout.cancel timeout

    $scope.$watchCollection 'model', (value) ->
      # Reset the auth forms after five minutes of inactivity
      if timeout
        $timeout.cancel timeout

      # If the model is not empty, start the timeout
      if value and not angular.equals(value, {})
        timeout = $timeout ->
          $scope.form?.$setPristine()
          $scope.model = null
          flash 'info',
            'For your security, the forms have been reset due to inactivity.'
        , 300000


configure = ['$provide', 'identityProvider', ($provide, identityProvider) ->
  identityProvider.checkAuthorization = [
    'session',
    (session) ->
      session.load().$promise
  ]

  identityProvider.forgetAuthorization = [
    'session',
    (session) ->
      session.logout({}).$promise
  ]

  identityProvider.requestAuthorization = [
    '$q', '$rootScope',
    ($q,   $rootScope) ->
      deferred = $q.defer()
      $rootScope.$on 'session', (event, data) -> deferred.resolve data
      deferred.promise
  ]
]


angular.module('h.auth', imports, configure)
.controller('AuthController', AuthController)
